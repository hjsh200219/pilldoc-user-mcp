"""요양기관기호 관련 도구들"""

import re
from typing import Dict, Optional, Tuple, List
from mcp.server.fastmcp import FastMCP


# 지역코드 매핑 (웹사이트에서 수집한 정보 기반)
REGION_CODES = {
    "11": "서울특별시",
    "12": "서울특별시", 
    "13": "서울특별시",
    "21": "부산광역시",
    "31": "경기도, 인천광역시",
    "32": "강원특별자치도",
    "33": "충청북도",
    "34": "대전광역시, 충청남도",
    "35": "전북특별자치도",
    "36": "전라남도",
    "37": "대구광역시, 경상북도",
    "38": "경상남도",
    "39": "제주특별자치도",
    "41": "경기도, 인천광역시"
}

# 종별구분 코드
INSTITUTION_TYPES = {
    "1": "종합병원",
    "2": "병원 (요양병원 포함, 4번째 자리가 8)",
    "3": "의원", 
    "4": "치과병원",
    "5": "치과의원",
    "6": "조산원",
    "7": "보건소",
    "8": "약국",
    "9": "한의원"
}


def validate_medical_institution_code(code: str) -> Dict:
    """
    요양기관기호 유효성 검증 및 정보 추출
    
    Args:
        code: 8자리 요양기관기호
        
    Returns:
        Dict: 검증 결과 및 추출된 정보
    """
    result = {
        "is_valid": False,
        "code": code,
        "region": None,
        "institution_type": None,
        "is_long_term_care_hospital": False,
        "serial_number": None,
        "check_digit": None,
        "errors": []
    }
    
    # 기본 형식 검증
    if not code or not isinstance(code, str):
        result["errors"].append("코드가 제공되지 않았습니다")
        return result
    
    # 숫자만 포함되는지 확인
    if not code.isdigit():
        result["errors"].append("코드는 숫자만 포함해야 합니다")
        return result
        
    # 8자리인지 확인
    if len(code) != 8:
        result["errors"].append("코드는 8자리여야 합니다")
        return result
    
    # 각 자리수별 정보 추출
    region_code = code[:2]  # 1-2자리: 지역구분
    institution_code = code[2]  # 3자리: 종별구분
    fourth_digit = code[3]  # 4자리: 요양병원 구분자 확인용
    serial_number = code[3:7]  # 4-7자리: 일련번호
    check_digit = code[7]  # 8자리: 체크번호
    
    # 지역코드 검증
    if region_code not in REGION_CODES:
        result["errors"].append(f"유효하지 않은 지역코드: {region_code}")
    else:
        result["region"] = {
            "code": region_code,
            "name": REGION_CODES[region_code]
        }
    
    # 종별구분 검증
    if institution_code not in INSTITUTION_TYPES:
        result["errors"].append(f"유효하지 않은 종별구분 코드: {institution_code}")
    else:
        result["institution_type"] = {
            "code": institution_code,
            "name": INSTITUTION_TYPES[institution_code]
        }
        
        # 요양병원 특별 규칙 확인
        if institution_code == "2" and fourth_digit == "8":
            result["is_long_term_care_hospital"] = True
            result["institution_type"]["name"] = "요양병원"
    
    result["serial_number"] = serial_number
    result["check_digit"] = check_digit
    
    # 오류가 없으면 유효한 것으로 판단
    if not result["errors"]:
        result["is_valid"] = True
    
    return result


def get_region_institutions(region_code: str) -> Dict:
    """
    특정 지역의 요양기관 정보 조회
    
    Args:
        region_code: 2자리 지역코드
        
    Returns:
        Dict: 지역 정보 및 가능한 기관 유형들
    """
    if region_code not in REGION_CODES:
        return {
            "error": f"유효하지 않은 지역코드: {region_code}",
            "available_codes": list(REGION_CODES.keys())
        }
    
    return {
        "region_code": region_code,
        "region_name": REGION_CODES[region_code],
        "available_institution_types": INSTITUTION_TYPES,
        "code_format": f"{region_code}XXXXXX (X는 종별구분, 일련번호, 체크번호)"
    }


def register_medical_institution_tools(mcp: FastMCP):
    """요양기관기호 관련 도구들을 MCP 서버에 등록"""
    
    @mcp.tool("validate_medical_institution_code")
    def validate_code_tool(code: str) -> Dict:
        """
        요양기관기호 유효성 검증 및 정보 추출
        
        Args:
            code: 8자리 요양기관기호 (예: "12281234")
            
        Returns:
            검증 결과 및 추출된 정보 (지역, 기관종별, 요양병원 여부 등)
        """
        return validate_medical_institution_code(code)
    
    @mcp.tool("get_region_medical_institutions") 
    def get_region_tool(region_code: str) -> Dict:
        """
        특정 지역의 요양기관 정보 조회
        
        Args:
            region_code: 2자리 지역코드 (예: "11", "21", "31")
            
        Returns:
            지역 정보 및 가능한 기관 유형들
        """
        return get_region_institutions(region_code)
    
    @mcp.tool("list_all_region_codes")
    def list_regions_tool() -> Dict:
        """
        모든 지역코드 목록 조회
        
        Returns:
            전체 지역코드와 지역명 매핑
        """
        return {
            "region_codes": REGION_CODES,
            "institution_types": INSTITUTION_TYPES,
            "total_regions": len(REGION_CODES),
            "usage_guide": {
                "code_format": "RRTTSSSSN (RR:지역, T:종별, SSSS:일련번호, N:체크번호)",
                "special_rules": {
                    "long_term_care_hospital": "3자리가 '2'이고 4자리가 '8'인 경우 요양병원"
                }
            }
        }
    
    @mcp.tool("analyze_medical_institution_pattern")
    def analyze_pattern_tool(codes: List[str]) -> Dict:
        """
        여러 요양기관기호의 패턴 분석
        
        Args:
            codes: 요양기관기호 리스트
            
        Returns:
            지역별, 종별별 분포 분석 결과
        """
        analysis = {
            "total_codes": len(codes),
            "valid_codes": 0,
            "invalid_codes": 0,
            "region_distribution": {},
            "institution_type_distribution": {},
            "long_term_care_hospitals": 0,
            "invalid_code_details": []
        }
        
        for code in codes:
            validation_result = validate_medical_institution_code(code)
            
            if validation_result["is_valid"]:
                analysis["valid_codes"] += 1
                
                # 지역별 분포
                region_name = validation_result["region"]["name"]
                analysis["region_distribution"][region_name] = analysis["region_distribution"].get(region_name, 0) + 1
                
                # 종별 분포  
                institution_name = validation_result["institution_type"]["name"]
                analysis["institution_type_distribution"][institution_name] = analysis["institution_type_distribution"].get(institution_name, 0) + 1
                
                # 요양병원 카운트
                if validation_result["is_long_term_care_hospital"]:
                    analysis["long_term_care_hospitals"] += 1
            else:
                analysis["invalid_codes"] += 1
                analysis["invalid_code_details"].append({
                    "code": code,
                    "errors": validation_result["errors"]
                })
        
        return analysis
