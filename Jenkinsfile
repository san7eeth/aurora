def collectPytestReport(String suite, String target, String junitFile, boolean coverage = false) {
    def name = "aurora-${suite}-${env.BUILD_NUMBER}"
    def options = "-e DATABASE_URL=sqlite+aiosqlite:////tmp/aurora-${suite}.db"
    def reportArgs = "--junitxml=/test-results/${junitFile}"
    if (coverage) reportArgs += " --cov=app --cov-report=xml:/test-results/coverage.xml"
    sh "docker create --name ${name} ${options} --entrypoint pytest ${env.BACKEND_TEST_IMAGE} ${target} -v --tb=short ${reportArgs}"
    def result = sh(returnStatus: true, script: "docker start -a ${name}")
    sh "mkdir -p test-results; docker cp ${name}:/test-results/. test-results/ || true; docker rm -f ${name} >/dev/null"
    if (result != 0) error("${suite} pytest suite failed (exit ${result})")
}

pipeline {
    agent any

    environment {
        BACKEND_TEST_IMAGE = "aurora-backend-test:${BUILD_NUMBER}"
        BACKEND_IMAGE = "aurora-backend:${BUILD_NUMBER}"
        FRONTEND_IMAGE = "aurora-frontend:${BUILD_NUMBER}"
        COMPOSE_PROJECT = "aurora-ci-${BUILD_NUMBER}"
        SONAR_HOST_URL = "http://host.docker.internal:9000"
    }

    options {
        timestamps()
        timeout(time: 90, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        skipDefaultCheckout(true)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log --oneline -5'
                sh 'printf "Branch: %s\\nCommit: %s\\n" "$BRANCH_NAME" "$GIT_COMMIT"'
            }
        }

        stage('Install') {
            steps {
                echo 'Build reproducible backend test/runtime and frontend tool images.'
                sh 'docker build --target test -t "$BACKEND_TEST_IMAGE" ./backend'
                sh 'docker build --target lint -t aurora-frontend-lint:${BUILD_NUMBER} ./frontend'
            }
        }

        stage('Lint') {
            steps {
                sh 'docker run --rm --entrypoint flake8 "$BACKEND_TEST_IMAGE" app/ --max-line-length=120 --count --statistics'
                echo 'Frontend lint ran as a required stage in the frontend lint image build.'
            }
        }

        stage('Unit Tests') {
            steps {
                script { collectPytestReport('unit', 'tests/unit/', 'unit.xml', true) }
            }
        }

        stage('Integration Tests') {
            steps {
                script { collectPytestReport('integration', 'tests/integration/', 'integration.xml') }
            }
        }

        stage('UI Tests') {
            steps {
                sh 'mkdir -p test-results'
                sh 'BACKEND_BIND_ADDRESS=0.0.0.0 AURORA_BACKEND_IMAGE="$BACKEND_IMAGE" AURORA_FRONTEND_IMAGE="$FRONTEND_IMAGE" docker compose -p "$COMPOSE_PROJECT" up -d --build aurora-backend aurora-frontend'
                sh '''
                    for attempt in $(seq 1 60); do
                      if curl -fsS http://host.docker.internal:8000/health >/dev/null; then break; fi
                      sleep 2
                    done
                    curl -fsS http://host.docker.internal:8000/health >/dev/null
                '''
                sh 'AURORA_BACKEND_IMAGE="$BACKEND_IMAGE" AURORA_FRONTEND_IMAGE="$FRONTEND_IMAGE" docker compose -p "$COMPOSE_PROJECT" --profile qa build aurora-e2e'
                script {
                    def network = sh(returnStdout: true, script: 'docker inspect --format="{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}" $(AURORA_BACKEND_IMAGE="$BACKEND_IMAGE" AURORA_FRONTEND_IMAGE="$FRONTEND_IMAGE" docker compose -p "$COMPOSE_PROJECT" ps -q aurora-backend)').trim()
                    def name = "aurora-e2e-${env.BUILD_NUMBER}"
                    sh "docker create --name ${name} --network ${network} -e CI=true -e AURORA_URL=http://aurora-frontend -e BACKEND_URL=http://aurora-backend:8000 -e PLAYWRIGHT_OUTPUT_DIR=/tmp/playwright-results aurora-e2e:local"
                    def result = sh(returnStatus: true, script: "docker start -a ${name}")
                    sh "docker cp ${name}:/tmp/playwright-results/. test-results/ || true; docker rm -f ${name} >/dev/null"
                    if (result != 0) error("Playwright UI/API smoke checks failed (exit ${result})")
                }
            }
        }

        stage('Java QA Module') {
            steps {
                sh 'BACKEND_URL=http://host.docker.internal:8000 mvn -B -f qa-java/pom.xml -Dtest=AuroraAPITest,AuroraBDDTest test'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'qa-java/target/surefire-reports/*.xml'
                    archiveArtifacts artifacts: 'qa-java/target/cucumber-report.html,qa-java/target/cucumber-results.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Security Checks') {
            steps {
                sh 'docker run --rm --entrypoint bandit "$BACKEND_TEST_IMAGE" -r app/ --severity-level medium -f json -o /dev/stdout > bandit-report.json'
                sh 'docker run --rm --entrypoint pip-audit "$BACKEND_TEST_IMAGE" -r requirements.txt'
                sh 'gitleaks detect --source . --redact --no-banner --report-format json --report-path gitleaks-report.json'
            }
            post {
                always { archiveArtifacts artifacts: 'bandit-report.json,gitleaks-report.json', allowEmptyArchive: true }
            }
        }

        stage('Build') {
            steps {
                sh 'docker build -t "$BACKEND_IMAGE" ./backend'
                sh 'docker build --build-arg VITE_WS_BASE=ws://localhost:8000 -t "$FRONTEND_IMAGE" ./frontend'
            }
        }

        stage('SonarQube Analysis') {
            when { anyOf { branch 'main'; branch 'develop' } }
            steps {
                withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                    sh '''sonar-scanner \
                      -Dsonar.host.url="$SONAR_HOST_URL" \
                      -Dsonar.token="$SONAR_TOKEN" \
                      -Dsonar.projectKey=aurora \
                      -Dsonar.projectName="Aurora AI Assistant" \
                      -Dsonar.sources=backend/app,frontend/src \
                      -Dsonar.tests=backend/tests,e2e-playwright/tests,qa-java/src/test/java \
                      -Dsonar.python.version=3.12 \
                      -Dsonar.python.coverage.reportPaths=test-results/coverage.xml \
                      -Dsonar.qualitygate.wait=true'''
                }
            }
        }

        stage('Package') {
            when { anyOf { branch 'main'; buildingTag() } }
            steps {
                sh '''
                  mkdir -p release
                  docker save "$BACKEND_IMAGE" "$FRONTEND_IMAGE" -o "release/aurora-images-${BUILD_NUMBER}.tar"
                  frontend_container="aurora-frontend-package-${BUILD_NUMBER}"
                  docker create --name "$frontend_container" "$FRONTEND_IMAGE" >/dev/null
                  mkdir -p release/frontend-dist
                  docker cp "$frontend_container:/usr/share/nginx/html/." release/frontend-dist/
                  docker rm "$frontend_container" >/dev/null
                  zip -qr "release/aurora-frontend-${BUILD_NUMBER}.zip" release/frontend-dist
                  printf 'build=%s\\ncommit=%s\\ncreated_utc=%s\\n' "$BUILD_NUMBER" "$GIT_COMMIT" "$(date -u +%FT%TZ)" > release/manifest.txt
                  sha256sum "release/aurora-images-${BUILD_NUMBER}.tar" "release/aurora-frontend-${BUILD_NUMBER}.zip" release/manifest.txt > release/SHA256SUMS
                '''
                archiveArtifacts artifacts: 'release/**', fingerprint: true
            }
        }

        stage('Deploy Staging') {
            when { branch 'develop' }
            steps {
                input message: 'All required checks passed. Deploy this build to local staging?', ok: 'Deploy staging'
                sh 'docker build --build-arg VITE_WS_BASE=ws://localhost:18000 -t aurora-frontend:${BUILD_NUMBER}-staging ./frontend'
                sh 'STAGING_BIND_ADDRESS=0.0.0.0 AURORA_BACKEND_IMAGE="$BACKEND_IMAGE" AURORA_FRONTEND_IMAGE="aurora-frontend:${BUILD_NUMBER}-staging" docker compose -p aurora-staging -f docker-compose.yml -f docker-compose.staging.yml up -d --no-build --remove-orphans'
                sh '''
                  for attempt in $(seq 1 30); do
                    if curl -fsS http://host.docker.internal:18000/health >/dev/null; then exit 0; fi
                    sleep 2
                  done
                  echo "Staging health check failed. Use scripts/rollback-staging.sh with the previous backend image tag."
                  exit 1
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'test-results/*.xml'
            archiveArtifacts artifacts: 'test-results/**', allowEmptyArchive: true
            sh 'docker compose -p "$COMPOSE_PROJECT" down --remove-orphans || true'
            deleteDir()
        }
        success { echo "✅ All required stages passed — ${env.JOB_NAME} #${env.BUILD_NUMBER}" }
        failure { echo "❌ Build failed. Review the first red pipeline stage and its archived report." }
        unstable { echo '⚠️ Build is unstable; review test reports before merging.' }
    }
}
