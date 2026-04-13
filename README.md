# Abnormal Change Detection Agent

VLM 기반 이상 변경 분석 에이전트 프로젝트 문서 모음이다. 이 프로젝트는 순찰/패트롤 과정에서 수집되는 이전 정상 이미지와 현재 이미지를 비교하고, 1차 이상 변경 검출 결과를 함께 활용하여 실제 이상 유형을 판단하고 조치 권고까지 생성하는 것을 목표로 한다.

## 문서 구성

- `docs/project-overview.md`: 프로젝트 목표, 범위, 산출물 정의
- `docs/requirements.md`: 기능/비기능 요구사항, 입출력, 제약사항
- `docs/system-architecture.md`: 처리 단계와 모듈 구조
- `docs/harness-engineering-plan.md`: 하네스 엔지니어링 기반 검증/평가 전략
- `docs/abnormal-taxonomy.md`: 이상 유형 분류 기준 초안
- `docs/action-guidelines.md`: 초기 조치 권고 가이드 초안
- `docs/prompt-template.md`: 운영용 VLM 프롬프트 템플릿 초안
- `docs/model-provider-setup.md`: 사내/외부 모델 호출 설정 방법
- `docs/usage.md`: 실제 실행 절차와 설정 입력 방법
- `docs/agent-workflow.md`: 에이전트 전체 처리 흐름과 파일 맵
- `docs/development-log.md`: 개발 로그, 의사결정, 이슈 관리 템플릿
- `docs/open-questions.md`: 사용자 확인이 필요한 항목 정리

## 프로젝트 한 줄 설명

이전 정상 이미지, 현재 이미지, 1차 이상 시각화 이미지를 입력으로 받아 작업장 이상 변경 유형을 판별하고, 근거 텍스트와 조치 권고를 산출하는 비대화형 VLM 에이전트를 구축한다.

## 현재 기준 처리 흐름

1. 이미지 로드
2. 이미지 정렬 및 전처리
3. 1차 이상 변경 시각화 이미지에서 유의 영역 해석
4. 전체 이미지와 패치 영역에 대한 VLM 분석
5. 분석 결과 통합 및 최종 이상 유형 도출
6. 조치 권고 생성

## 실행/개발 원칙

- Python 기반으로 구현한다.
- Python 버전은 `3.11`을 기준으로 한다.
- VLM 호출은 현재 개발/검증 단계에서 `GPT-5.4` 연결 기준으로 설계하고, 추후 사내 모델 `Kimi-K2.5`로 전환 가능한 구조를 유지한다.
- `requirements.txt`, 실행 명령어, 입력 디렉터리 규약은 개발 과정에서 지속 업데이트한다.
- 결과물은 추론 결과뿐 아니라 중간 분석 로그까지 보존할 수 있도록 설계한다.
- 일반적인 이상 변경 판정은 반드시 VLM 절차를 거치며, rule-based 로직은 앵글 오류 또는 입력 이상 케이스를 거르는 보조 용도로만 사용한다.

## 현재 샘플 데이터 규약

- `test_images/` 아래에는 현재 개발용 샘플 입력 케이스가 정리되어 있다.
- 현재 샘플은 `test_images/<spot>/<case>/` 구조를 사용한다.
- 각 케이스 폴더는 아래 3개 파일을 가진다.
- `time_0.jpeg`: 이전 정상 이미지
- `time_n.png`: 현재 이미지
- `dino_time_n.png`: 현재 이미지에 대응하는 1차 이상 시각화 이미지
- 예시: `test_images/spot_1/time_3/`
- 운영용 파일명 규약과 별도로, 개발 초기에는 이 샘플 규약도 함께 지원한다.

## 현재 실행 방법

- 케이스 탐색만 수행:
- `py -3.11 -m src.main --input-dir test_images --mode discover`
- 샘플 파이프라인 실행:
- `py -3.11 -m src.main --input-dir test_images --output-dir outputs`
- JSON 형태로 결과 요약 출력:
- `py -3.11 -m src.main --input-dir test_images --output-dir outputs --output-format json`

기본 분석기 선택 규칙:

- `config/runtime.local.json`이 없으면 `mock` 분석기 사용
- `config/runtime.local.json`에 `endpoint_url`이 있으면 `compatible_api` 사용 가능
- 강제 지정: `--backend mock` 또는 `--backend compatible_api`

- 케이스별 출력 파일: `outputs/<spot>/<case>/result.json`, `report.md`, `prompt_system.txt`, `prompt_user.txt`
- 실행 요약 파일: `outputs/run_summary.json`

실제 모델 호출 정보 입력 위치:

- 파일 경로: `config/runtime.local.json`
- 예시 파일: `config/runtime.example.json`
- 상세 템플릿: `config/runtime.local.template.jsonc`
- 상세 사용법: `docs/model-provider-setup.md`

## 우선 산출물

- 실행 가능한 메인 파이프라인
- 입력/출력 폴더 규약
- 평가용 테스트셋 구조
- 하네스 기반 검증 시나리오와 측정 지표
- 개발 로그 및 의사결정 기록 체계

## 기본 출력 형식

- 구조화 결과 `JSON`
- 사람 검토용 `Markdown` 리포트

기본 `JSON` 핵심 필드:

- `abnormal_type`: 간단한 단어 중심 이상 변경 요약 설명
- `analysis_log`: VLM 이상 분석 진행 중 생성된 전체 텍스트 기록
- `abnormal_report`: 통합 정리된 이상 검출 유형 내용
- `action_guide`: 이상 검출 결과 기반 조치 권고 사항

## 다음 작업 권장 순서

1. `docs/open-questions.md`의 미결정 사항 확정
2. 입력 데이터셋 구조와 출력 JSON 스키마 확정
3. 메인 파이프라인 및 하네스 골격 구현
4. 샘플 데이터 기반 평가 루프 구성
