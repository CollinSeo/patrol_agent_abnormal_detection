# 사용 방법

이 문서는 이 프로젝트를 실제로 실행하는 방법을 한 번에 따라할 수 있도록 정리한 실행 가이드다.

## 1. 준비

### Python 버전 확인

```bash
py -3.11 --version
```

### 의존성 설치

```bash
py -3.11 -m pip install -r requirements.txt
```

## 2. 입력 데이터 위치

현재 샘플 입력은 아래 경로에 있다.

- `test_images/spot_1/time_1/`
- `test_images/spot_1/time_2/`
- `test_images/spot_1/time_3/`
- `test_images/spot_1/time_4/`
- `test_images/spot_1/time_5/`

각 케이스 폴더는 아래 3개 파일을 가진다.

- `time_0.jpeg`: 이전 정상 이미지
- `time_n.png`: 현재 이미지
- `dino_time_n.png`: 1차 이상 시각화 이미지

## 3. 실행 전 가장 중요한 설정 위치

실제 모델 호출 정보는 반드시 아래 파일에 넣는다.

- `config/runtime.local.json`

예시 템플릿 파일은 아래에 있다.

- `config/runtime.example.json`
- `config/runtime.local.template.jsonc`

`runtime.local.json`은 `.gitignore`에 포함되어 있어 커밋되지 않는다.

## 4. 회사 모델 Kimi-K2.5 연결 방법

### 4-1. 설정 파일 생성

`config/runtime.example.json`을 복사해서 아래 파일을 만든다.

- `config/runtime.local.json`

### 4-2. 실제 값 입력

회사에서 받은 값을 아래처럼 입력한다.

```json
{
  "analyzer_backend": "compatible_api",
  "provider_name": "company-kimi",
  "model_name": "Kimi-K2.5",
  "endpoint_url": "https://your-company-endpoint.example.com/v1/chat/completions",
  "api_key": "YOUR_API_KEY_HERE",
  "headers": {
    "Authorization": "Bearer YOUR_API_KEY_HERE"
  },
  "timeout_seconds": 120
}
```

더 구체적인 주석 포함 템플릿은 아래 파일을 참고하면 된다.

- `config/runtime.local.template.jsonc`

### 4-3. 각 항목 의미

- `analyzer_backend`: 회사 모델 호출 시 `compatible_api`
- `provider_name`: 리포트에 남길 이름 예: `company-kimi`
- `model_name`: 실제 모델 이름 예: `Kimi-K2.5`
- `endpoint_url`: 회사가 제공한 실제 API URL
- `api_key`: 회사가 제공한 API key 또는 token
- `headers`: 회사 서비스가 요구하는 추가 헤더
- `timeout_seconds`: 요청 제한 시간

## 5. 실행 명령

### 케이스 탐색만 확인

```bash
py -3.11 -m src.main --input-dir test_images --mode discover
```

### mock 분석기로 실행

실제 모델 연결 전 구조 검증용이다.

```bash
py -3.11 -m src.main --input-dir test_images --output-dir outputs --backend mock
```

### 회사 모델로 실제 실행

```bash
py -3.11 -m src.main --input-dir test_images --output-dir outputs --backend compatible_api
```

### JSON 요약을 콘솔에 출력

```bash
py -3.11 -m src.main --input-dir test_images --output-dir outputs --backend compatible_api --output-format json
```

## 6. 결과 확인 위치

실행 후 결과는 아래 위치에 저장된다.

- 케이스별 JSON: `outputs/<spot>/<case>/result.json`
- 케이스별 Markdown: `outputs/<spot>/<case>/report.md`
- 시스템 프롬프트: `outputs/<spot>/<case>/prompt_system.txt`
- 사용자 프롬프트: `outputs/<spot>/<case>/prompt_user.txt`
- 전체 요약: `outputs/run_summary.json`

예시:

- `outputs/spot_1/time_1/result.json`
- `outputs/spot_1/time_1/report.md`

## 7. 문제 발생 시 확인 순서

### 설정 파일이 없을 때

- `config/runtime.local.json`이 없으면 실제 모델 대신 `mock` 분석기로만 동작한다.

### endpoint_url이 틀렸을 때

- 회사가 준 API 주소가 정확한지 확인한다.
- `/v1/chat/completions` 경로까지 포함해야 하는지 확인한다.

### 인증 오류가 날 때

- `api_key` 값 확인
- `Authorization` 헤더 형식 확인
- 사내 게이트웨이 전용 헤더 요구사항 확인

### 응답 파싱 오류가 날 때

- 회사 API가 OpenAI 호환 `chat/completions` 형식인지 확인
- 멀티모달 이미지 입력을 지원하는지 확인
- JSON schema 응답 강제를 지원하는지 확인

## 8. 회사에 확인해야 할 항목

실제 연결 전에 아래 정보를 받으면 된다.

1. `endpoint_url`
2. `model_name`
3. `api_key`
4. 추가 헤더 필요 여부
5. 이미지 입력 형식 지원 여부
6. OpenAI 호환 `chat/completions` 지원 여부

## 9. 관련 문서

- 상세 모델 설정: `docs/model-provider-setup.md`
- 에이전트 워크플로우: `docs/agent-workflow.md`
- 프롬프트 템플릿: `docs/prompt-template.md`
- 요구사항: `docs/requirements.md`
