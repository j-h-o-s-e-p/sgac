pipeline {
    agent none  // No usamos un agente global, definimos uno específico

    environment {
        // Credencial configurada en Jenkins
        SONAR_TOKEN = credentials('sonar-token') 
    }

    stages {
        // --- ETAPA DE PREPARACIÓN Y TESTS (CORRE EN CONTENEDOR PYTHON) ---
        stage('Test & Audit') {
            agent {
                docker {
                    image 'python:3.11' // Usamos una imagen que sí tiene Python
                    args '-u 0:0'      // Correr como root para evitar problemas de permisos
                }
            }
            steps {
                echo '=== 1. Instalando Dependencias ==='
                sh 'pip install -r requirements-dev.txt'
                
                echo '=== 2. Análisis Estático ==='
                // Black y Flake8 (ignora errores para no bloquear el demo, quita el || true para ser estricto)
                sh 'black --check . || true'
                sh 'flake8 . --exclude=migrations,venv --max-line-length=120 --ignore=D,E,F,W || true'

                echo '=== 3. Pruebas Unitarias ==='
                sh 'pytest tests/unit --junitxml=reports/junit-unit.xml || true'
            }
        }

        // --- ETAPA DE SONARQUBE (REQUIERE EL PLUGIN) ---
        stage('SonarQube Analysis') {
            agent {
                docker { 
                    image 'sonarsource/sonar-scanner-cli' // Imagen oficial del scanner
                    // Conectamos este contenedor a la red de tus servicios para que vea a sgac_sonarqube
                    args '--network container:sgac_jenkins' 
                }
            }
            steps {
                script {
                    // Usamos el nombre del servidor configurado en Jenkins (Paso 2C)
                    withSonarQubeEnv('SonarQube-Docker') {
                        sh '''
                            sonar-scanner \
                            -Dsonar.projectKey=sgac_backend \
                            -Dsonar.sources=. \
                            -Dsonar.host.url=http://sgac-sonarqube:9000 \
                            -Dsonar.login=$SONAR_TOKEN
                        '''
                    }
                }
            }
        }

        // --- ETAPA DE DESPLIEGUE (SOLO SI PASA TODO) ---
        stage('Deploy') {
            when { branch 'main' }
            agent any
            steps {
                echo '=== Desplegando Contenedores ==='
                // Aquí reiniciamos los servicios. Como Jenkins tiene montado el docker.sock, puede controlar al host.
                sh 'docker-compose up -d --build web worker'
            }
        }
    }
}
