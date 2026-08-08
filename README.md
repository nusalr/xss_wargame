# xss_wargame

1. 문제 개요 및 목표
XSS 취약점에 관한 간단한 워게임 문제입니다.

2. 실행 방법
Docker 사용을 추천합니다.
 -> Docker Desktop 실행
 -> powershell 창에서
  cd xss_wargame/xss-wargame (코드가 있는 폴더 내부로 이동)
  Copy-Item .env.example .env (env.example 파일을 env이름으로 복사해 .env 파일을 생성 )
  docker compose up --build
 -> 로컬 주소 접속 (http://127.0.0.1:8000)
 -> 문제 풀기

3. XSS유형 및 취약점 
 이 워게임에는 XSS 취약점 중 DOM-based XSS 유형의 취약점이 존재합니다.
 취약점이 있는 코드는 app.py의 /vuln 페이지와 vuln.html에서 확인할 수 있습니다.
 app.py에서 /vuln 페이지의 동작을 보면, vuln.html에 param을 받아 전달합니다.
 이후 vuln.html 페이지에서 <script> 단락을 확인해보면, 클라이언트가 직접 입력하는 param 값을 innerHTML에 그대로 대입하고 있는 것을 볼 수 있습니다.
 이 부분에서 취약점이 발생합니다.

4. innerHTML이 취약점이 발생하는 이유
 기본적으로 innerHTML은 내부적으로 <script> 태그를 실행하지 않습니다. 그러나 <script> 태그가 아닌 <img src > 같은 태그를 사용하게 되면, innerHTML이 제어할 수 없기 때문에 이 부분에서 보안상의 위험이 생길 수 있습니다. 또한 onerror 이벤트를 이미지 태그와 같이 사용함으로서 javascript를 실행하여 클라이언트의 쿠키를 훔쳐올 수 있습니다. 
