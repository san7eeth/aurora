pipeline {
    agent any

    environment {
        VENV      = 'backend/.venv'
        PYTEST    = "${VENV}/bin/pytest"
        PIP       = "${VENV}/bin/pip"
        FLAKE8    = "${VENV}/bin/flake8"
        BANDIT    = "${VENV}/bin/bandit"
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout') {
            steps {
                echo '── Checkout ──────────────────────────'
                checkout scm
                sh 'git log --oneline -5'
                sh 'echo "Branch: ${GIT_BRANCH}"'
            }
        }

        stage('Install') {
            steps {
                echo '── Install Python Dependencies ────────'
                sh '''
                    python3.12 -m venv backend/.venv 2>/dev/null || python3 -m venv backend/.venv
                    backend/.venv/bin/pip install --upgrade pip setuptools wheel -q
                    backend/.venv/bin/pip install -r backend/requirements.txt -q
                    backend/.venv/bin/pip install \
                        pytest pytest-asyncio httpx pytest-cov \
                        flake8 bandit -q
                '''
            }
        }

        stage('Lint') {
            steps {
                echo '── Lint: flake8 ───────────────────────'
                sh '''
                    backend/.venv/bin/flake8 backend/app/ \
                        --max-line-length=120 \
                        --exclude=__pycache__,migrations \
                        --format=pylint \
                        --output-file=flake8-report.txt || true
                    echo "=== Lint Results ==="
                    cat flake8-report.txt || echo "No issues found"
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'flake8-report.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Unit Tests') {
            steps {
                echo '── Unit Tests ─────────────────────────'
                sh 'mkdir -p test-results'
                dir('backend') {
                    sh '''
                        ../.venv/bin/pytest tests/unit/ -v \
                            --tb=short \
                            --junitxml=../test-results/unit.xml \
                            --cov=app \
                            --cov-report=xml:../coverage.xml \
                            --cov-report=html:../htmlcov/ \
                            -m "not integration and not slow" || true
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results/unit.xml'
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('Integration Tests') {
            steps {
                echo '── Integration Tests ──────────────────'
                dir('backend') {
                    sh '''
                        ../.venv/bin/pytest tests/integration/ -v \
                            --tb=short \
                            --junitxml=../test-results/integration.xml \
                            -m "integration" || true
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results/integration.xml'
                }
            }
        }

        stage('Security Scan') {
            steps {
                echo '── Security: bandit ───────────────────'
                sh '''
                    backend/.venv/bin/bandit -r backend/app/ \
                        -f json -o bandit-report.json \
                        --severity-level medium -q || true
                    backend/.venv/bin/bandit -r backend/app/ \
                        --severity-level high || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('SonarQube Analysis') {
            when {
                anyOf { branch 'main'; branch 'develop' }
            }
            steps {
                echo '── SonarQube Scan ─────────────────────'
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                            -Dsonar.projectKey=aurora \
                            -Dsonar.projectName="Aurora AI Assistant" \
                            -Dsonar.sources=backend/app \
                            -Dsonar.tests=backend/tests \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.python.flake8.reportPaths=flake8-report.txt || true
                    '''
                }
            }
        }

        stage('Docker Build') {
            when {
                anyOf { branch 'main'; branch 'develop' }
            }
            steps {
                echo '── Docker Build ───────────────────────'
                sh '''
                    docker build -t aurora-backend:${BUILD_NUMBER} ./backend
                    docker tag aurora-backend:${BUILD_NUMBER} aurora-backend:latest
                    echo "Image: aurora-backend:${BUILD_NUMBER}"
                '''
            }
        }

        stage('Frontend Build') {
            when {
                anyOf { branch 'main'; branch 'develop' }
            }
            steps {
                echo '── Frontend Build ─────────────────────'
                sh '''
                    cd frontend
                    npm ci --silent
                    npm run build
                    echo "Frontend build: OK"
                '''
            }
            post {
                success {
                    archiveArtifacts artifacts: 'frontend/dist/**', allowEmptyArchive: true
                }
            }
        }

        stage('Deploy Staging') {
            when { branch 'develop' }
            steps {
                echo '── Deploy Staging ─────────────────────'
                sh '''
                    docker compose down aurora-backend --remove-orphans || true
                    docker compose up -d aurora-backend
                    sleep 15
                    curl -sf http://localhost:8000/health && \
                        echo "Staging: HEALTHY" || \
                        (echo "Staging: UNHEALTHY" && exit 1)
                '''
            }
        }

        stage('Package Release') {
            when { branch 'main' }
            steps {
                echo '── Package Release ────────────────────'
                sh '''
                    echo "Release packaging: Aurora v${BUILD_NUMBER}"
                    echo "TODO Phase 10: PyInstaller packaging"
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline finished: ${currentBuild.currentResult}"
            cleanWs(notFailBuild: true)
        }
        success {
            echo "✅ BUILD PASSED — ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        failure {
            echo "❌ BUILD FAILED — ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        unstable {
            echo "⚠️ BUILD UNSTABLE (test failures) — ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
