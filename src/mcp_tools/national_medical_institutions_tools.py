"""전국 의료기관 데이터 도구들 - PostgreSQL salesdb institutions 테이블"""
import os
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None
import json


def register_national_medical_institutions_tools(mcp: FastMCP) -> None:
    """전국 의료기관 데이터 도구들 등록 (PostgreSQL salesdb institutions 테이블)"""

    # institutions 테이블 컬럼 정보 (스키마 가이드)
    INSTITUTIONS_COLUMNS = {
        'id': 'TEXT PRIMARY KEY',
        'name': 'TEXT NOT NULL', 
        'open_date': 'TEXT',
        'phone': 'TEXT',
        'address': 'TEXT',
        'type': 'TEXT',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'latitude': 'DOUBLE PRECISION',
        'longitude': 'DOUBLE PRECISION',
        'emdongNm': 'TEXT',  # 읍면동명
        'sgguCdNm': 'TEXT',  # 시군구명 (올바른 컬럼명)
        'sidoCdNm': 'TEXT'   # 시도명 (올바른 컬럼명)
    }

    def validate_column_name(column_name: str) -> str:
        """컬럼명 유효성 검사 및 자동 수정 (PostgreSQL 따옴표 처리)"""
        # 대소문자 구분 없이 매핑
        column_mapping = {
            'sidocdnm': '"sidoCdNm"',
            'sigungucdnm': '"sgguCdNm"', 
            'sggucdnm': '"sgguCdNm"',
            'emdngnm': '"emdongNm"',
            'emdongname': '"emdongNm"',
            'sidoCdNm': '"sidoCdNm"',
            'sgguCdNm': '"sgguCdNm"',
            'emdongNm': '"emdongNm"'
        }
        
        lower_name = column_name.lower()
        if lower_name in column_mapping:
            return column_mapping[lower_name]
        
        # 정확한 컬럼명인지 확인하고 따옴표 추가
        if column_name in INSTITUTIONS_COLUMNS:
            return f'"{column_name}"'
            
        return f'"{column_name}"'  # 모든 컬럼명에 따옴표 추가

    def get_db_connection():
        """데이터베이스 연결 생성"""
        if psycopg2 is None:
            raise ImportError("psycopg2 is not installed. Install it with: pip install psycopg2-binary")
        
        # 환경 변수에서 데이터베이스 연결 정보 가져오기
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        
        # 개별 환경 변수로 연결 (claude_desktop_config.json에서 로드됨)
        host = os.getenv('POSTGRES_HOST')
        port = os.getenv('POSTGRES_PORT')
        user = os.getenv('POSTGRES_USER')
        password = os.getenv('POSTGRES_PASSWORD')
        database = os.getenv('POSTGRES_DB')
        
        return psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

    @mcp.tool()
    def get_institutions(
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        institution_type: Optional[str] = None,
        region: Optional[str] = None,
        order_by: str = "id",
        order_direction: str = "ASC"
    ) -> Dict[str, Any]:
        """institutions 테이블에서 데이터를 조회합니다.
        
        Args:
            limit: 조회할 최대 레코드 수 (기본: 100)
            offset: 건너뛸 레코드 수 (페이징용, 기본: 0)
            search: 기관명 검색어 (부분 검색)
            institution_type: 기관 유형 필터
            region: 지역 필터
            order_by: 정렬 기준 컬럼 (기본: id)
            order_direction: 정렬 방향 (ASC/DESC, 기본: ASC)
            
        Returns:
            조회된 institutions 데이터와 메타 정보
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 기본 쿼리
            base_query = "SELECT * FROM institutions"
            count_query = "SELECT COUNT(*) FROM institutions"
            conditions = []
            params = []
            
            # 검색 조건 추가
            if search:
                conditions.append("name ILIKE %s")
                params.append(f"%{search}%")
            
            if institution_type:
                conditions.append("type ILIKE %s")
                params.append(f"%{institution_type}%")
                
            if region:
                # region 파라미터는 sidoCdNm 또는 sgguCdNm에서 검색
                sido_col = validate_column_name('sidoCdNm')
                sigungu_col = validate_column_name('sgguCdNm')
                region_condition = f"({sido_col} ILIKE %s OR {sigungu_col} ILIKE %s)"
                conditions.append(region_condition)
                params.append(f"%{region}%")
                params.append(f"%{region}%")
            
            # WHERE 절 구성
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
                base_query += where_clause
                count_query += where_clause
            
            # 총 개수 조회
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # 정렬 및 페이징
            order_direction = order_direction.upper()
            if order_direction not in ['ASC', 'DESC']:
                order_direction = 'ASC'
                
            base_query += f" ORDER BY {order_by} {order_direction}"
            base_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 데이터 조회
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            # 결과를 딕셔너리 리스트로 변환
            data = [dict(row) for row in results]
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": data,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "current_page": (offset // limit) + 1,
                    "total_pages": (total_count + limit - 1) // limit,
                    "has_next": offset + limit < total_count,
                    "has_prev": offset > 0
                },
                "filters": {
                    "search": search,
                    "institution_type": institution_type,
                    "region": region,
                    "order_by": order_by,
                    "order_direction": order_direction
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e)
            }

    @mcp.tool()
    def get_institution_by_id(institution_id: int) -> Dict[str, Any]:
        """ID로 특정 institution 조회
        
        Args:
            institution_id: 조회할 institution의 ID
            
        Returns:
            해당 institution 데이터
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM institutions WHERE id = %s", (institution_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return {
                    "success": True,
                    "data": dict(result)
                }
            else:
                return {
                    "success": False,
                    "error": "not_found",
                    "message": f"Institution with ID {institution_id} not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e)
            }

    @mcp.tool()
    def get_institutions_schema() -> Dict[str, Any]:
        """institutions 테이블의 스키마 정보 조회
        
        Returns:
            테이블 스키마 정보 (컬럼명, 데이터 타입 등)
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'institutions' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "table_name": "institutions",
                "columns": [dict(col) for col in columns]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e)
            }

    @mcp.tool()
    def get_institutions_stats() -> Dict[str, Any]:
        """institutions 테이블의 통계 정보 조회
        
        Returns:
            테이블 통계 정보 (총 레코드 수, 유형별 분포 등)
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 총 레코드 수
            cursor.execute("SELECT COUNT(*) as total_count FROM institutions")
            total_count = cursor.fetchone()['total_count']
            
            # 기관 유형별 분포
            cursor.execute("""
                SELECT institution_type, COUNT(*) as count 
                FROM institutions 
                WHERE institution_type IS NOT NULL 
                GROUP BY institution_type 
                ORDER BY count DESC
            """)
            type_distribution = cursor.fetchall()
            
            # 지역별 분포
            cursor.execute("""
                SELECT region, COUNT(*) as count 
                FROM institutions 
                WHERE region IS NOT NULL 
                GROUP BY region 
                ORDER BY count DESC 
                LIMIT 20
            """)
            region_distribution = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "stats": {
                    "total_count": total_count,
                    "type_distribution": [dict(row) for row in type_distribution],
                    "region_distribution": [dict(row) for row in region_distribution]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e)
            }

    @mcp.tool()
    def execute_institutions_query(
        query: str,
        params: Optional[List] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """institutions 테이블에 대한 커스텀 SQL 쿼리 실행
        
        Args:
            query: 실행할 SQL 쿼리 (SELECT만 허용)
            params: 쿼리 파라미터 리스트
            limit: 결과 제한 수
            
        Returns:
            쿼리 실행 결과
        """
        try:
            # 보안을 위해 SELECT 쿼리만 허용
            query_upper = query.strip().upper()
            if not query_upper.startswith('SELECT'):
                return {
                    "success": False,
                    "error": "invalid_query",
                    "message": "Only SELECT queries are allowed"
                }
            
            # institutions 테이블 관련 쿼리인지 확인
            if 'institutions' not in query.lower():
                return {
                    "success": False,
                    "error": "invalid_query",
                    "message": "Query must reference institutions table"
                }
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # LIMIT 추가 (보안상 결과 제한)
            if 'LIMIT' not in query_upper:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params or [])
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": [dict(row) for row in results],
                "query": query,
                "row_count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e),
                "query": query
            }

    @mcp.tool()
    def get_institutions_distribution_by_region_and_type(
        sido_name: Optional[str] = None,
        sigungu_name: Optional[str] = None,
        institution_type: Optional[str] = None,
        group_by: str = "sido",
        limit: int = 100
    ) -> Dict[str, Any]:
        """전국 시도 및 시군구별 기관 종별(type) 분포를 조회합니다.
        
        Args:
            sido_name: 특정 시도로 필터링 (부분 검색, 예: '서울')
            sigungu_name: 특정 시군구로 필터링 (부분 검색, 예: '강남')
            institution_type: 특정 기관 종별로 필터링 (예: '의원', '병원')
            group_by: 그룹화 방식 ('sido': 시도별, 'sigungu': 시군구별, 'type': 종별만, 'all': 시도+시군구+종별)
            limit: 결과 제한 수 (기본: 100)
            
        Returns:
            지역별 기관 종별 분포 통계
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 기본 조건
            conditions = []
            params = []
            
            # 필터 조건 추가 (컬럼명 검증 적용)
            if sido_name:
                sido_col = validate_column_name("sidoCdNm")
                conditions.append(f"{sido_col} ILIKE %s")
                params.append(f"%{sido_name}%")
                
            if sigungu_name:
                sigungu_col = validate_column_name("sgguCdNm")
                conditions.append(f"{sigungu_col} ILIKE %s")
                params.append(f"%{sigungu_name}%")
                
            if institution_type:
                conditions.append("type ILIKE %s")
                params.append(f"%{institution_type}%")
            
            # WHERE 절 구성
            where_clause = ""
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)
            
            # 컬럼명 검증
            sido_col = validate_column_name("sidoCdNm")
            sigungu_col = validate_column_name("sgguCdNm")
            
            # 그룹화 방식에 따른 쿼리 구성
            if group_by == "sido":
                # 시도별 종별 분포
                query = f"""
                    SELECT 
                        {sido_col} as sido_name,
                        type,
                        COUNT(*) as count
                    FROM institutions
                    {where_clause}
                    GROUP BY {sido_col}, type
                    ORDER BY {sido_col}, count DESC
                    LIMIT %s
                """
                
            elif group_by == "sigungu":
                # 시군구별 종별 분포
                query = f"""
                    SELECT 
                        {sido_col} as sido_name,
                        {sigungu_col} as sigungu_name,
                        type,
                        COUNT(*) as count
                    FROM institutions
                    {where_clause}
                    GROUP BY {sido_col}, {sigungu_col}, type
                    ORDER BY {sido_col}, {sigungu_col}, count DESC
                    LIMIT %s
                """
                
            elif group_by == "type":
                # 전국 종별 분포만
                query = f"""
                    SELECT 
                        type,
                        COUNT(*) as count
                    FROM institutions
                    {where_clause}
                    GROUP BY type
                    ORDER BY count DESC
                    LIMIT %s
                """
                
            else:  # group_by == "all"
                # 시도+시군구+종별 전체 분포
                query = f"""
                    SELECT 
                        {sido_col} as sido_name,
                        {sigungu_col} as sigungu_name,
                        type,
                        COUNT(*) as count
                    FROM institutions
                    {where_clause}
                    GROUP BY {sido_col}, {sigungu_col}, type
                    ORDER BY {sido_col}, {sigungu_col}, count DESC
                    LIMIT %s
                """
            
            params.append(limit)
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # 추가 통계 정보
            summary_query = f"""
                SELECT 
                    COUNT(*) as total_institutions,
                    COUNT(DISTINCT {sido_col}) as total_sido,
                    COUNT(DISTINCT {sigungu_col}) as total_sigungu,
                    COUNT(DISTINCT type) as total_types
                FROM institutions
                {where_clause}
            """
            cursor.execute(summary_query, params[:-1])  # limit 제외
            summary = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": [dict(row) for row in results],
                "summary": dict(summary),
                "filters": {
                    "sido_name": sido_name,
                    "sigungu_name": sigungu_name,
                    "institution_type": institution_type,
                    "group_by": group_by,
                    "limit": limit
                },
                "query_info": {
                    "group_by": group_by,
                    "result_count": len(results)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e)
            }

    @mcp.tool()
    def get_institutions_top_regions_by_type(
        institution_type: str,
        group_by: str = "sido",
        top_n: int = 10
    ) -> Dict[str, Any]:
        """특정 기관 종별로 상위 지역들을 조회합니다.
        
        Args:
            institution_type: 조회할 기관 종별 (예: '의원', '병원', '약국')
            group_by: 그룹화 방식 ('sido': 시도별, 'sigungu': 시군구별)
            top_n: 상위 N개 지역 (기본: 10)
            
        Returns:
            특정 기관 종별 상위 지역 순위
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 컬럼명 검증
            sido_col = validate_column_name("sidoCdNm")
            sigungu_col = validate_column_name("sgguCdNm")
            
            if group_by == "sido":
                query = f"""
                    SELECT 
                        {sido_col} as region_name,
                        type,
                        COUNT(*) as count,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                    FROM institutions
                    WHERE type ILIKE %s
                    GROUP BY {sido_col}, type
                    ORDER BY count DESC
                    LIMIT %s
                """
            else:  # sigungu
                query = f"""
                    SELECT 
                        {sido_col} as sido_name,
                        {sigungu_col} as sigungu_name,
                        CONCAT({sido_col}, ' ', {sigungu_col}) as region_name,
                        type,
                        COUNT(*) as count,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                    FROM institutions
                    WHERE type ILIKE %s
                    GROUP BY {sido_col}, {sigungu_col}, type
                    ORDER BY count DESC
                    LIMIT %s
                """
            
            cursor.execute(query, (f"%{institution_type}%", top_n))
            results = cursor.fetchall()
            
            # 전체 통계
            total_query = """
                SELECT COUNT(*) as total_count
                FROM institutions 
                WHERE type ILIKE %s
            """
            cursor.execute(total_query, (f"%{institution_type}%",))
            total_count = cursor.fetchone()['total_count']
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": [dict(row) for row in results],
                "summary": {
                    "institution_type": institution_type,
                    "total_count": total_count,
                    "group_by": group_by,
                    "showing_top": min(top_n, len(results))
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e)
            }

    @mcp.tool()
    def get_institutions_comparison_by_regions(
        regions: List[str],
        comparison_type: str = "sido"
    ) -> Dict[str, Any]:
        """여러 지역 간 기관 종별 분포를 비교합니다.
        
        Args:
            regions: 비교할 지역 리스트 (예: ['서울', '부산', '대구'])
            comparison_type: 비교 방식 ('sido': 시도 비교, 'sigungu': 시군구 비교)
            
        Returns:
            지역 간 기관 종별 분포 비교 결과
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 컬럼명 검증
            sido_col = validate_column_name("sidoCdNm")
            sigungu_col = validate_column_name("sgguCdNm")
            
            # 지역별 데이터 수집
            comparison_data = []
            
            for region in regions:
                if comparison_type == "sido":
                    query = f"""
                        SELECT 
                            %s as region,
                            type,
                            COUNT(*) as count
                        FROM institutions
                        WHERE {sido_col} ILIKE %s
                        GROUP BY type
                        ORDER BY count DESC
                    """
                    cursor.execute(query, (region, f"%{region}%"))
                else:  # sigungu
                    query = f"""
                        SELECT 
                            %s as region,
                            type,
                            COUNT(*) as count
                        FROM institutions
                        WHERE {sigungu_col} ILIKE %s
                        GROUP BY type
                        ORDER BY count DESC
                    """
                    cursor.execute(query, (region, f"%{region}%"))
                
                region_data = cursor.fetchall()
                comparison_data.extend([dict(row) for row in region_data])
            
            # 전체 종별 목록
            all_types_query = """
                SELECT DISTINCT type, COUNT(*) as total_count
                FROM institutions 
                GROUP BY type 
                ORDER BY total_count DESC
            """
            cursor.execute(all_types_query)
            all_types = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "comparison_data": comparison_data,
                "all_types": [dict(row) for row in all_types],
                "regions_compared": regions,
                "comparison_type": comparison_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "database_error",
                "message": str(e)
            }

    @mcp.tool()
    def get_institutions_column_guide() -> Dict[str, Any]:
        """institutions 테이블의 컬럼 가이드 정보를 제공합니다.
        
        Returns:
            컬럼명, 데이터 타입, 설명이 포함된 가이드
        """
        return {
            "success": True,
            "table_name": "institutions",
            "columns": INSTITUTIONS_COLUMNS,
            "column_descriptions": {
                "id": "기관 고유 ID (TEXT, PRIMARY KEY)",
                "name": "기관명 (TEXT, NOT NULL)",
                "open_date": "개설일 (TEXT)",
                "phone": "전화번호 (TEXT)",
                "address": "주소 (TEXT)",
                "type": "기관 종별 (TEXT) - 의원, 병원, 약국 등",
                "created_at": "생성일시 (TIMESTAMP)",
                "latitude": "위도 (DOUBLE PRECISION)",
                "longitude": "경도 (DOUBLE PRECISION)",
                "emdongNm": "읍면동명 (TEXT)",
                "sgguCdNm": "시군구명 (TEXT) - 강남구, 서초구 등",
                "sidoCdNm": "시도명 (TEXT) - 서울특별시, 경기도 등"
            },
            "common_mistakes": {
                "sidocdnm": "올바른 컬럼명: sidoCdNm",
                "sigungucdnm": "올바른 컬럼명: sgguCdNm", 
                "sggucdnm": "올바른 컬럼명: sgguCdNm",
                "emdngnm": "올바른 컬럼명: emdongNm"
            },
            "usage_examples": {
                "서울시 필터링": "WHERE sidoCdNm LIKE '%서울%'",
                "강남구 필터링": "WHERE sgguCdNm LIKE '%강남%'",
                "의원 필터링": "WHERE type = '의원'",
                "시도별 그룹화": "GROUP BY sidoCdNm",
                "시군구별 그룹화": "GROUP BY sidoCdNm, sgguCdNm"
            }
        }
