# Agent Workflow

이 문서는 현재 구현된 에이전트가 어떤 입력을 받고, 어떤 단계로 처리하며, 어디에 결과를 저장하는지 운영 관점에서 설명한다.

## 목적

에이전트는 이전 정상 이미지, 현재 이미지, 1차 이상 시각화 이미지를 함께 사용해 작업장 내 실제 이상 변경을 판정하고 구조화된 결과와 리포트를 생성한다.

## 입력

현재 지원 입력은 다음 두 가지다.

### 1. 샘플 규약

- 경로: `test_images/<spot>/<case>/`
- 파일:
- `time_0.jpeg`: 이전 정상 이미지
- `time_n.png`: 현재 이미지
- `dino_time_n.png`: 1차 이상 시각화 이미지

### 2. 운영 규약

- 경로: 임의 케이스 폴더
- 파일:
- `<timestamp>_SPOT.<ext>` 2개
- `dino_<current_timestamp>_SPOT.<ext>` 1개

## 전체 워크플로우

1. 실행 시작
2. 런타임 설정 로드
3. 입력 케이스 탐색
4. SIFT 기반 정렬 및 품질 판정
5. 케이스별 프롬프트 생성
6. 분석기 선택
7. 모델 호출 또는 mock 처리
8. 결과 구조화
9. 케이스별 파일 저장
10. 전체 실행 요약 저장

## 단계별 설명

### 1. 실행 시작

진입점은 `src/main.py`다.

대표 명령:

```bash
py -3.11 -m src.main --input-dir test_images --output-dir outputs --backend compatible_api
```

### 2. 런타임 설정 로드

설정 로딩 위치:

- `src/config.py`

설정 소스 우선순위:

1. 환경 변수
2. `config/runtime.local.json`
3. 기본값

주요 설정 항목:

- `analyzer_backend`
- `provider_name`
- `model_name`
- `endpoint_url`
- `api_key`
- `headers`
- `timeout_seconds`

### 3. 입력 케이스 탐색

입력 로더 위치:

- `src/loaders/case_loader.py`

로더는 입력 루트 아래의 디렉터리를 순회하며 이미지 파일 세트를 찾는다.

찾아낸 케이스는 `AnalysisCase` 객체로 변환된다.

핵심 필드:

- `case_id`
- `spot_id`
- `case_dir`
- `reference_image_path`
- `current_image_path`
- `diff_visualization_path`
- `input_scheme`

### 4. SIFT 기반 정렬 및 품질 판정

정렬 위치:

- `src/preprocess/alignment.py`

이 단계에서 수행하는 일:

- 이전 정상 이미지와 현재 이미지 간 SIFT 특징점 추출
- Lowe ratio test 기반 good match 선택
- RANSAC homography 추정
- 현재 이미지와 diff 시각화 이미지에 동일 변환 적용
- 비중첩 영역 블랙 마스킹
- 정렬 품질 평가

현재 정렬 실패 판단에 사용하는 주요 지표:

- good match 수
- inlier 수
- inlier 비율
- 정렬 후 overlap 비율
- 코너 이동량 비율
- 투영 면적 비율

정렬 품질이 기준에 미달하면 해당 케이스는 더 이상 이상 분석으로 보내지 않고 `앵글 변경`으로 종료한다.

### 5. 케이스별 프롬프트 생성

프롬프트 로딩 위치:

- `src/prompts/template_loader.py`

원본 문서:

- `docs/prompt-template.md`

이 단계에서 다음 2개가 준비된다.

- 시스템 프롬프트
- 사용자 프롬프트

사용자 프롬프트에는 아래 값이 주입된다.

- `case_id`
- `spot_id`
- `reference_image_path`
- `current_image_path`
- `diff_visualization_path`

### 6. 분석기 선택

선택 로직 위치:

- `src/main.py`

지원 백엔드:

- `mock`
- `compatible_api`

동작 방식:

- `mock`: 모델 호출 없이 구조 검증용 결과 생성
- `compatible_api`: 회사의 OpenAI 호환 API 엔드포인트 호출

### 7. 모델 호출 또는 mock 처리

#### mock 분석기

위치:

- `src/analyzers/mock_analyzer.py`

역할:

- 입력 경로와 프롬프트 연결이 정상인지 확인
- 실제 모델 없이 파이프라인 전체를 검증

#### compatible_api 분석기

위치:

- `src/analyzers/compatible_api_analyzer.py`

역할:

- 시스템 프롬프트와 사용자 프롬프트를 조합
- 이미지 3장을 base64 data URL로 변환
- `chat/completions` 형식으로 요청 전송
- JSON schema 응답 파싱

요청에 포함되는 이미지:

1. 이전 정상 이미지
2. 현재 이미지
3. 1차 이상 시각화 이미지

### 8. 결과 구조화

결과 모델 위치:

- `src/results/models.py`

분석 결과는 `CaseOutput`으로 정리된다.

주요 필드:

- `case_id`
- `spot_id`
- `status`
- `abnormal_detected`
- `primary_category`
- `abnormal_type`
- `analysis_log`
- `abnormal_report`
- `action_guide`
- `decision_basis`
- `ignored_factors`
- `prompt_version`
- `model_info`
- `input_paths`

### 9. 케이스별 파일 저장

출력 작성 위치:

- `src/reporting/writers.py`

케이스별 저장 파일:

- `result.json`
- `report.md`
- `prompt_system.txt`
- `prompt_user.txt`

저장 경로 규칙:

- `outputs/<spot>/<case>/`

예:

- `outputs/spot_1/time_1/result.json`
- `outputs/spot_1/time_1/report.md`

### 10. 전체 실행 요약 저장

전체 실행이 끝나면 아래 파일이 생성된다.

- `outputs/run_summary.json`

현재 포함 내용:

- 전체 케이스 수
- 상태별 개수
- 이상 유형별 개수

## 현재 구현 상태

이미 구현된 부분:

- 입력 케이스 자동 탐색
- 프롬프트 템플릿 로딩
- mock 분석기
- 회사용 compatible API 분석기
- JSON/Markdown 출력 저장
- 실행 요약 저장

아직 고도화 여지가 있는 부분:

- 실제 전처리/정렬 품질 점검 로직
- 시각화 이미지의 패치 좌표 정밀 해석
- 재시도 정책
- 에러 분류 고도화
- 하네스 정답 비교 자동화

## 운영자가 실제로 하는 일

운영자가 해야 하는 일은 크게 4개다.

1. 입력 이미지 폴더 준비
2. `config/runtime.local.json`에 회사 모델 호출 정보 입력
3. CLI 명령 실행
4. `outputs/` 결과 확인

## 회사 환경에서 가장 중요한 체크포인트

1. `endpoint_url`이 완전한지 확인
2. `model_name`이 실제 배포 모델명과 일치하는지 확인
3. 인증 헤더 형식이 맞는지 확인
4. 회사 API가 이미지 입력을 지원하는지 확인
5. 회사 API가 OpenAI 호환 `chat/completions`를 지원하는지 확인

## 관련 파일 맵

- 실행 진입점: `src/main.py`
- 설정 로더: `src/config.py`
- 입력 로더: `src/loaders/case_loader.py`
- 프롬프트 로더: `src/prompts/template_loader.py`
- 모델 호출: `src/analyzers/compatible_api_analyzer.py`
- 결과 모델: `src/results/models.py`
- 출력 기록: `src/reporting/writers.py`
- 파이프라인 오케스트레이션: `src/pipeline.py`

## 권장 운영 순서

1. `--mode discover`로 케이스 인식 확인
2. `--backend mock`으로 출력 구조 확인
3. `config/runtime.local.json` 작성
4. `--backend compatible_api`로 실제 추론 실행
5. `outputs/.../result.json`과 `report.md` 검토
