"""
offer情报局 REST API 客户端。

职责单一：封装 HTTP 请求，只暴露业务方法，不包含过滤/输出逻辑。
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .auth import TokenManager


class OfferAPI:
    """offer情报局 API 薄封装。"""

    def __init__(self, base_url: str = "https://offerqingbaoju.cn/api", timeout: int = 30):
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._token_mgr = TokenManager()
        self._session = requests.Session()
        retry = Retry(
            total=4,
            connect=4,
            read=4,
            status=4,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    # ---- public: navigation metadata ----

    def list_navigations(self) -> list[dict]:
        """获取所有可用的数据导航列表。"""
        return self._get("/simple/navigations")

    def get_navigation(self, nav_id: int) -> dict | None:
        """获取单个导航详情（含字段定义）。"""
        resp = self._get(f"/csv/files/{nav_id}/columns")
        return resp

    # ---- public: job data ----

    def fetch_jobs(
        self,
        nav_id: int,
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """
        拉取指定导航下的岗位数据。

        返回 {"data": [...], "total": int, "page": int, ...}
        """
        return self._get(
            f"/simple/navigation/{nav_id}/data",
            params={"page": page, "page_size": page_size},
        )

    def fetch_all_jobs(
        self,
        nav_id: int,
        max_records: int = 500,
    ) -> list[dict]:
        """分页拉取全部岗位数据，直到无更多数据或达到上限。"""
        all_data = []
        page = 1
        while len(all_data) < max_records:
            resp = self.fetch_jobs(nav_id, page=page)
            records = resp.get("data", [])
            if not records:
                break
            all_data.extend(records)
            pagination = resp.get("pagination", {})
            total = pagination.get("total_rows", 0)
            if total and len(all_data) >= total:
                break
            if not pagination.get("has_next", False):
                break
            page += 1
        return all_data[:max_records]

    # ---- internal ----

    def _headers(self) -> dict:
        token = self._token_mgr.get_token()
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self._base}{path}"
        resp = self._session.get(
            url, headers=self._headers(), params=params, timeout=self._timeout
        )
        if resp.status_code == 401:
            refreshed = self._token_mgr.refresh_access_token()
            if refreshed:
                resp = self._session.get(
                    url,
                    headers={"Authorization": f"Bearer {refreshed}"},
                    params=params,
                    timeout=self._timeout,
                )
        resp.raise_for_status()
        return resp.json()
