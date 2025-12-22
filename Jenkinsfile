pipeline {
    agent any

    environment {
        PYTHONDONTWRITEBYTECODE = '1'
        DISABLE_FILE_LOGGING = '1'
    }

    stages {

        stage('Setup') {
            steps {
                echo '=== Instalando Dependencias ==='
                sh 'pip install -r requirements-dev.txt'
            }
        }

        stage('Code Quality') {
            steps {
                echo '=== Black & Flake8 ==='
                sh 'black --check .'
                sh 'flake8 . --exclude=migrations,venv --max-line-length=120'
            }
        }

        stage('Security Audit') {
            steps {
                echo '=== Bandit ==='
                sh '''
                    bandit -r . \
                        -x ./tests,./venv \
                        -f json \
                        -o bandit-report.json || true
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo '=== Tests Unitarios ==='
                sh '''
                    mkdir -p reports
                    pytest -m unit \
                        --junitxml=reports/junit-unit.xml \
                        --cov=. \
                        --cov-report=xml
                '''
            }
        }

        stage('Integration Tests') {
            steps {
                echo '=== Tests de Integración ==='
                sh '''
                    pytest -m integration \
                        --junitxml=reports/junit-integration.xml
                '''
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo '=== Deploy ==='
                sh 'docker-compose up -d --build'
            }
        }
    }

    post {
        always {
            junit 'reports/**/*.xml'
            archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
        }

        success {
            echo '✅ Pipeline ejecutado correctamente'
        }

        failure {
            echo '❌ Pipeline falló'
        }
    }
}

