pipeline {
  agent any
  options { disableConcurrentBuilds(); timestamps(); skipStagesAfterUnstable(); timeout(time: 30, unit: 'MINUTES'); buildDiscarder(logRotator(numToKeepStr: '20')) }
  triggers { pollSCM('H/5 * * * *') }
  environment { IMAGE = "scm-app:${BUILD_NUMBER}" }
  stages {
    stage('Checkout') {
      steps { git branch: 'main', url: 'https://github.com/sozhanrl/SCM.git' }
    }
    stage('Docker build') {
      steps {
        writeFile file: '.dockerignore', text: '.git\n.env\n.venv\ninstance\nuploads\n__pycache__\n.pytest_cache\nreports\n'
        writeFile file: 'Dockerfile.jenkins-app', text: '''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
COPY . .
RUN mkdir -p instance uploads
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--access-logfile", "-", "wsgi:app"]
'''
        writeFile file: 'wsgi.py', text: '''from app import create_app
from app.extensions import db
app = create_app('production')
# This deployment is served over local HTTP.
app.config['SESSION_COOKIE_SECURE'] = False
with app.app_context():
    db.create_all()
'''
        sh 'docker build -f Dockerfile.jenkins-app -t "$IMAGE" .'
      }
    }
    stage('pytest') {
      steps {
        sh '''mkdir -p reports
rm -f reports/results.xml
name="scm-tests-$BUILD_NUMBER"
docker create --name "$name" "$IMAGE" python -m pytest -q --junitxml=/tmp/results.xml
set +e
docker start -a "$name"
status=$(docker inspect -f '{{.State.ExitCode}}' "$name")
docker cp "$name:/tmp/results.xml" reports/results.xml
copy_status=$?
docker rm "$name"
set -e
[ "$copy_status" -eq 0 ] || exit "$copy_status"
exit "$status"
'''
      }
      post { always { junit 'reports/results.xml' } }
    }
    stage('Deploy') {
      steps {
        sh '''set -eu
docker volume inspect scm_database >/dev/null
docker volume inspect scm_uploads >/dev/null
# Keep the previous container available for rollback.
if docker container inspect scm-app-previous >/dev/null 2>&1; then docker rm scm-app-previous; fi
if docker container inspect scm-app >/dev/null 2>&1; then
  docker stop scm-app
  docker rename scm-app scm-app-previous
fi
rollback() {
  docker logs scm-app || true
  docker rm -f scm-app || true
  if docker container inspect scm-app-previous >/dev/null 2>&1; then
    docker rename scm-app-previous scm-app
    docker start scm-app
  fi
}
trap rollback EXIT
docker run -d --name scm-app --restart unless-stopped -p 127.0.0.1:5000:5000 --env-file /var/jenkins_home/scm-runtime.env -e DATABASE_URL=sqlite:////app/instance/elden_care.db -e UPLOAD_FOLDER=/app/uploads -v scm_database:/app/instance -v scm_uploads:/app/uploads "$IMAGE"
healthy=0
for attempt in $(seq 1 30); do
  if docker exec scm-app python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=3)"; then healthy=1; break; fi
  sleep 2
done
if [ "$healthy" -ne 1 ]; then
  exit 1
fi
trap - EXIT
'''
      }
    }
  }
}
