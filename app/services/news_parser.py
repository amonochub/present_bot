"""
Парсер новостей с mos.ru с улучшениями согласно Context7
"""

import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, SoupStrainer

from app.schemas.news import CacheInfo, NewsCard, NewsResponse, RateLimitInfo

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter для защиты от превышения лимитов запросов"""

    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def can_request(self, key: str) -> bool:
        """Проверить, можно ли выполнить запрос"""
        now = time.time()
        # Очищаем старые запросы
        self.requests[key] = [
            req_time for req_time in self.requests[key] if now - req_time < self.window
        ]

        if len(self.requests[key]) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True

    def get_rate_limit_info(self, key: str) -> RateLimitInfo:
        """Получить информацию о rate limiting"""
        now = time.time()
        # Очищаем старые запросы
        self.requests[key] = [
            req_time for req_time in self.requests[key] if now - req_time < self.window
        ]

        return RateLimitInfo(
            key=key,
            requests_count=len(self.requests[key]),
            max_requests=self.max_requests,
            window_seconds=self.window,
            can_request=len(self.requests[key]) < self.max_requests,
        )


class NewsParser:
    """Парсер новостей с официальных сайтов с улучшениями Context7"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        # Добавляем retry-логику согласно Context7
        from requests.adapters import HTTPAdapter
        from urllib3.util import Retry

        retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        # Кэширование согласно Context7
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(minutes=15)

        # Rate limiting согласно Context7
        self.rate_limiter = RateLimiter()

        # Базовый URL для валидации
        self.base_url = "https://www.mos.ru"

        # Настройка логирования согласно Context7
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    async def get_news_cards(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить карточки новостей с mos.ru с улучшенным кэшированием"""
        self.logger.info(f"Запрос новостей, лимит: {limit}")

        # Проверяем rate limiting
        if not self.rate_limiter.can_request("news_parser"):
            self.logger.warning("Превышен лимит запросов к парсеру новостей")
            return self._get_fallback_news()

        # Проверяем Redis кэш (если доступен)
        cache_key = f"news_cache:{limit}"
        try:
            from app.services.cache_service import redis_client
            import json
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                self.logger.info(f"Возвращаем новости из Redis кэша: {len(json.loads(cached_data))}")
                return json.loads(cached_data)
        except Exception as e:
            self.logger.warning(f"Redis кэш недоступен: {e}")

        # Проверяем локальный кэш согласно Context7
        cache_key_local = f"news_{limit}"
        now = datetime.now()

        if cache_key_local in self._cache:
            cached_data, cached_time = self._cache[cache_key_local]
            if now - cached_time < self._cache_ttl:
                self.logger.info(f"Возвращаем кэшированные новости из локального кэша: {len(cached_data)}")
                return cached_data

        try:
            url = "https://www.mos.ru/news/rubric/obrazovanie/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Проверка HTTP статуса согласно Context7

            # Оптимизированный парсинг с SoupStrainer согласно Context7
            strainer = SoupStrainer("div", class_=lambda x: x and "news" in x.lower())
            soup = BeautifulSoup(response.text, "html.parser", parse_only=strainer)

            news_cards = self._parse_news_cards(soup, limit)

            # Сохраняем в Redis кэш (если доступен)
            try:
                await redis_client.setex(cache_key, 300, json.dumps(news_cards))  # 5 минут TTL
                self.logger.info(f"Новости сохранены в Redis кэш")
            except Exception as e:
                self.logger.warning(f"Не удалось сохранить в Redis кэш: {e}")

            # Сохраняем в локальный кэш
            self._cache[cache_key_local] = (news_cards, now)
            self.logger.info(f"Получено {len(news_cards)} новостей")
            return news_cards

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка HTTP запроса: {e}")
            return self._get_fallback_news()
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при получении новостей: {e}", exc_info=True)
            return self._get_fallback_news()

    async def get_news_response(self, limit: int = 5) -> NewsResponse:
        """Получить новости в виде валидированного ответа"""
        try:
            raw_news = await self.get_news_cards(limit)

            # Валидируем каждую новость с помощью Pydantic
            validated_news = []
            for news_item in raw_news:
                try:
                    validated_card = NewsCard(**news_item)
                    validated_news.append(validated_card)
                except Exception as e:
                    self.logger.warning(f"Невалидная новость: {e}")
                    continue

            return NewsResponse(
                news=validated_news,
                total_count=len(validated_news),
                cached=False,  # TODO: добавить логику определения кэша
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Ошибка при создании NewsResponse: {e}")
            # Возвращаем пустой ответ с ошибкой
            return NewsResponse(news=[], total_count=0, cached=False, timestamp=datetime.now())

    def get_cache_info(self) -> CacheInfo:
        """Получить информацию о кэше"""
        now = datetime.now()
        cache_size = len(self._cache)

        # Находим самый старый кэш для определения TTL
        oldest_cache = None
        if self._cache:
            oldest_cache = min(self._cache.values(), key=lambda x: x[1])

        return CacheInfo(
            cache_key="news_cache",
            cached_at=oldest_cache[1] if oldest_cache else now,
            ttl_seconds=int(self._cache_ttl.total_seconds()),
            is_expired=(
                oldest_cache and (now - oldest_cache[1]) > self._cache_ttl
                if oldest_cache
                else False
            ),
            cache_size=cache_size,
        )

    def get_rate_limit_info(self) -> RateLimitInfo:
        """Получить информацию о rate limiting"""
        return self.rate_limiter.get_rate_limit_info("news_parser")

    def _parse_news_cards(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """Оптимизированный парсинг новостей согласно Context7"""
        news_cards = []

        # Пробуем разные селекторы для адаптивности
        selectors = ["div.news-card", "div.news-item", "article.news-card", "div.news-list__item"]

        cards: List[Any] = []
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                break

        if not cards:
            # Fallback - ищем любые карточки с новостями
            cards = soup.find_all("div", class_=lambda x: x and "news" in x.lower())

        for card in cards[:limit]:
            try:
                # Извлекаем данные более эффективно согласно Context7
                title_elem = card.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                title = title_elem.get_text(strip=True) if title_elem else ""

                link_elem = card.find("a", href=True)
                link = link_elem["href"] if link_elem else ""

                if title and link:
                    # Валидация URL согласно Context7
                    validated_url = self._validate_url(link, self.base_url)

                    news_card = {
                        "title": title,
                        "date": self._extract_date(card),
                        "desc": self._extract_description(card),
                        "url": validated_url,
                    }

                    # Валидация карточки согласно Context7
                    if self._validate_news_card(news_card):
                        news_cards.append(news_card)

            except Exception as e:
                self.logger.warning(f"Ошибка парсинга карточки: {e}")
                continue

        # Если не удалось получить новости, возвращаем заглушки
        if not news_cards:
            news_cards = self._get_fallback_news()

        return news_cards

    def _extract_date(self, card: Any) -> str:
        """Извлечь дату из карточки"""
        date_selectors = [".news-card__date", ".news-item__date", ".news-date", ".date"]

        for selector in date_selectors:
            found = card.select_one(selector)
            if found:
                return found.get_text(strip=True)
        return "Не указана"

    def _extract_description(self, card: Any) -> str:
        """Извлечь описание из карточки"""
        desc_selectors = [
            ".news-card__announce",
            ".news-item__description",
            ".news-description",
            ".description",
        ]

        for selector in desc_selectors:
            found = card.select_one(selector)
            if found:
                return found.get_text(strip=True)
        return "Описание недоступно"

    def _validate_url(self, url: str, base_url: str) -> str:
        """Валидация и нормализация URL согласно Context7"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                # Относительный URL
                url = urljoin(base_url, url)

            # Проверяем, что URL принадлежит разрешенному домену
            parsed = urlparse(url)
            if parsed.netloc not in ["www.mos.ru", "mos.ru"]:
                self.logger.warning(f"Подозрительный URL: {url}")
                return base_url

            return url
        except Exception as e:
            self.logger.warning(f"Ошибка валидации URL {url}: {e}")
            return base_url

    def _validate_news_card(self, card_data: Dict[str, Any]) -> bool:
        """Валидация карточки новости согласно Context7"""
        try:
            # Проверяем обязательные поля
            required_fields = ["title", "url"]
            for field in required_fields:
                if not card_data.get(field):
                    return False

            # Проверяем длину заголовка
            if len(card_data["title"]) < 5 or len(card_data["title"]) > 200:
                return False

            return True
        except Exception as e:
            self.logger.warning(f"Невалидная карточка новости: {e}")
            return False

    def _get_fallback_news(self) -> List[Dict[str, Any]]:
        """Заглушки новостей на случай недоступности сайта"""
        return [
            {
                "title": "Обновление системы образования",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "desc": "Внедрение новых технологий в образовательный процесс",
                "url": "https://www.mos.ru/donm/",
            },
            {
                "title": "Психологическая поддержка учащихся",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "desc": "Расширение сети психологических служб в школах",
                "url": "https://www.mos.ru/donm/",
            },
            {
                "title": "Подготовка к новому учебному году",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "desc": "Информация о подготовке школ к началу учебного года",
                "url": "https://www.mos.ru/donm/",
            },
        ]


# Глобальный экземпляр парсера
news_parser = NewsParser()


async def get_news_cards(limit: int = 5) -> List[Dict[str, Any]]:
    """Получить карточки новостей"""
    return await news_parser.get_news_cards(limit)


async def get_news_response(limit: int = 5) -> NewsResponse:
    """Получить валидированный ответ с новостями"""
    return await news_parser.get_news_response(limit)
