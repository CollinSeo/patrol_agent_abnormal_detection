# 모델 호출 설정 가이드

이 문서는 회사 환경에서 사내 서비스 모델 예: `Kimi-K2.5`를 연결하기 위한 설정 위치와 사용법을 설명한다.

## 핵심 원칙

- 모델 호출 정보는 코드에 직접 하드코딩하지 않는다.
- 실제 비밀값은 `config/runtime.local.json`에만 넣는다.
- 저장소에는 예시 파일 `config/runtime.example.json`만 유지한다.
- 주석이 포함된 실무용 템플릿은 `config/runtime.local.template.jsonc`를 참고한다.

## 정확한 설정 위치

실제 호출 정보는 아래 파일에 넣는다.

- `config/runtime.local.json`

참고용 상세 템플릿:

- `config/runtime.local.template.jsonc`

이 파일은 현재 `.gitignore`에 포함되어 있어 커밋 대상에서 제외된다.

## 가장 간단한 사용 절차

1. `config/runtime.example.json`을 복사해서 `config/runtime.local.json`을 만든다.
2. 회사 환경에서 받은 실제 값을 채운다.
3. 아래 명령으로 파이프라인을 실행한다.

```bash
py -3.11 -m src.main --input-dir test_images --output-dir outputs --backend compatible_api
```

## 파일 예시

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

실무용 주석 포함 버전은 아래 파일을 그대로 참고하면 된다.

- `config/runtime.local.template.jsonc`

## 필드 설명

- `analyzer_backend`: 실제 호출 백엔드 종류. 회사 환경에서는 `compatible_api` 사용.
- `provider_name`: 리포트에 남길 공급자 이름. 예: `company-kimi`
- `model_name`: 실제 모델명. 예: `Kimi-K2.5`
- `endpoint_url`: 회사 서비스가 제공하는 완전한 호출 URL. 현재 구현은 OpenAI 호환 `chat/completions` 형식을 기대한다.
- `api_key`: 기본 인증 토큰. `Authorization: Bearer ...` 형식이면 이 값만으로도 충분할 수 있다.
- `headers`: 추가 HTTP 헤더. 사내 게이트웨이가 별도 헤더를 요구하면 여기에 넣는다.
- `timeout_seconds`: 요청 타임아웃 초 단위.

## 인증 헤더 설정 방법

### 1. 일반적인 Bearer 토큰 방식

```json
{
  "api_key": "YOUR_API_KEY_HERE",
  "headers": {}
}
```

코드가 자동으로 `Authorization: Bearer <api_key>`를 추가한다.

### 2. 회사 전용 헤더 방식

```json
{
  "api_key": "",
  "headers": {
    "X-API-Key": "YOUR_API_KEY_HERE",
    "X-Project": "semiconductor-3s"
  }
}
```

이 경우 `headers` 값이 그대로 사용된다.

### 3. Bearer 토큰 + 추가 헤더 같이 사용

```json
{
  "api_key": "YOUR_API_KEY_HERE",
  "headers": {
    "X-Project": "semiconductor-3s"
  }
}
```

## 실행 명령

### 샘플 입력 실행

```bash
py -3.11 -m src.main --input-dir test_images --output-dir outputs --backend compatible_api
```

### 케이스 탐색만 수행

```bash
py -3.11 -m src.main --input-dir test_images --mode discover
```

## 출력 위치

- 케이스별 JSON: `outputs/<spot>/<case>/result.json`
- 케이스별 Markdown: `outputs/<spot>/<case>/report.md`
- 실제 전송된 프롬프트: `outputs/<spot>/<case>/prompt_system.txt`, `prompt_user.txt`
- 실행 요약: `outputs/run_summary.json`

## 중요한 호환 조건

현재 구현의 `compatible_api` 백엔드는 아래 형식을 기대한다.

- HTTP POST 기반
- OpenAI 호환 `chat/completions` 요청 형식
- 멀티모달 이미지 입력 지원
- `response_format.json_schema` 또는 이에 준하는 JSON 응답 강제 기능 지원

즉, 회사의 `Kimi-K2.5` 서비스가 OpenAI 호환 게이트웨이 형태로 제공되면 별도 코드 수정 없이 설정만 바꿔 실행할 수 있다.

## 만약 회사 서비스가 완전히 다른 API 형식이면

그 경우에도 구조는 이미 분리되어 있다.

- 호출 구현 위치: `src/analyzers/compatible_api_analyzer.py`
- 설정 로딩 위치: `src/config.py`
- 실행 연결 위치: `src/main.py`

이때는 요청 body 형식만 해당 사내 API 규격에 맞게 바꾸면 된다.

## 권장 점검 순서

1. 회사에서 `endpoint_url`, `model_name`, `api_key`, 추가 헤더 요구사항을 확인한다.
2. `config/runtime.local.json`에 값 입력
3. `--mode discover`로 입력 케이스 확인
4. `--backend compatible_api`로 실제 추론 실행
5. `outputs/.../result.json`에서 결과 확인
