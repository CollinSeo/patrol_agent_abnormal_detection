# 시스템 아키텍처

## 전체 흐름

1. 이미지 로드
2. 이미지 전처리/정렬/이상 변경 패치 처리
3. VLM 이상 분석
4. 분석 결과 통합/정리
5. 이상 유형 도출 및 조치 권고 생성

## 모듈 구조 초안

### 1. Input Loader

- 입력 루트 경로 순회
- 케이스 단위 파일 식별
- 파일 유효성 검사
- 메타데이터 구성
- 운영용 파일명 규약과 개발용 `test_images/<spot>/<case>/` 샘플 규약을 모두 지원

### 2. Preprocessor

- 이미지 로드
- 기준 이미지와 현재 이미지 정렬
- 해상도/색공간/크기 표준화
- 관심 영역 후보 추출
- 정렬 품질 점검 및 `앵글 변경` 판정

### 3. Patch Interpreter

- 1차 시각화 이미지에서 관심 영역 해석
- 파란색 영역과 빨간색 패치 정보를 구조화
- 기본적으로 시각화 이미지 전체를 VLM 입력에 포함
- 필요 시 추후 패치 단위 추가 이미지 또는 설명 생성으로 확장

### 4. VLM Analyzer

- 전체 이미지 비교 분석
- 패치 영역 집중 분석
- 이상 여부, 유형, 근거 문장 생성
- 원시 응답 로그 저장
- 일반 케이스에서는 최종 이상 판정을 위한 필수 단계로 사용

### 5. Result Integrator

- 전체 분석과 패치 분석의 충돌/보완 관계 정리
- 최종 이상 유형 선택
- 요약 설명 및 상세 설명 생성
- 판단 불가/모호 사례 처리
- 최종 `JSON`과 `Markdown` 리포트 출력 생성

### 6. Action Recommender

- 이상 유형 기반 초기 조치 권고 생성
- 향후 외부 매뉴얼 문서 기반 규칙 확장 예정

### 7. Harness Runner

- 케이스셋 실행 자동화
- 정답/기대값과 비교 평가
- 실패 사례 수집
- 회귀 검증 리포트 생성

## 권장 디렉터리 구조 초안

```text
    project-root/
  README.md
  requirements.txt
  docs/
    project-overview.md
    requirements.md
    system-architecture.md
    harness-engineering-plan.md
    abnormal-taxonomy.md
    action-guidelines.md
    development-log.md
    open-questions.md
  data/
    input/
      case_001/
      case_002/
    expected/
    outputs/
  src/
    main.py
    config.py
    loaders/
    preprocess/
    analyzers/
    integrators/
    recommenders/
    harness/
  tests/
```

## 인터페이스 원칙

- 입력 처리, 모델 호출, 결과 통합, 평가 로직은 분리한다.
- 모델 호출 계층은 API 제공자 변경에 독립적이어야 한다.
- 최종 결과 스키마는 하네스와 운영 파이프라인이 공통으로 사용한다.

## 실패 처리 원칙

- 필수 이미지 누락: 케이스 실패로 기록하고 다음 케이스 계속 수행
- 정렬 실패: `앵글 변경` 유형으로 기록하고 해당 케이스 분석 종료
- VLM 응답 오류: 재시도 정책 및 실패 로그 기록 필요
- 결과 충돌: `판단 불가` 또는 `검토 필요` 상태로 표기 가능

## 샘플 입력 메모

- 현재 저장소의 `test_images/`는 개발 초기 검증용 샘플 데이터셋이다.
- 각 케이스는 `spot` 하위의 `time_n` 폴더 단위로 구성된다.
- 로더는 이 구조를 우선 지원해 빠르게 파이프라인 검증이 가능해야 한다.

## 설계 의도

- 동일 위치 촬영이라도 미세한 앵글 차이와 조명 변화가 반복되므로 단순 이미지 직접 비교는 보조 수단으로만 사용한다.
- 구조적으로 잘못 수집된 케이스를 제외한 대부분의 이상 판단은 VLM의 문맥 기반 해석을 통해 수행한다.
