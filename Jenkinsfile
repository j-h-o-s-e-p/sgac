pipeline {
    agent any

    environment {
        PYTHONDONTWRITEBYTECODE = '1'
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements-dev.txt'
            }
        }

        stage('Code Quality (Black & Flake8)') {
            steps {
                echo '=== Verificando Estilo de Código ==='
                sh 'black --check .'
                sh 'flake8 .'
            }
        }

        stage('Security Audit (Bandit)') {
            steps {
                echo '=== Escaneo de Seguridad ==='
                sh 'bandit -r . -x ./tests,./venv'
            }
        }

        stage('Tests Execution') {
            steps {
                echo '=== Ejecutando Tests con Pytest & Coverage ==='
                sh 'mkdir -p reports'
                sh 'pytest --junitxml=reports/junit.xml'
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'docker-compose up -d --build'
            }
        }
    }
    
    post {
        always {
            junit 'reports/**/*.xml'
        }
    }
}
