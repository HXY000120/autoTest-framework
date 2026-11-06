// 黑马头条自动化框架 - Jenkins Pipeline（Windows agent / 自建 Runner）
// 依赖：Jenkins Allure Plugin；Web 阶段需本机浏览器，App 阶段需 adb 设备 + Appium 服务
pipeline {
    agent any

    parameters {
        booleanParam(name: 'RUN_REAL', defaultValue: false,
                     description: '真实环境联调（打开后才发真实请求用例）')
        booleanParam(name: 'RUN_WEB', defaultValue: false,
                     description: '执行 Web UI 用例（需本机浏览器）')
        booleanParam(name: 'RUN_APP', defaultValue: false,
                     description: '执行 App UI 用例（需真机/模拟器 + Appium）')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('准备环境') {
            steps {
                bat 'python -m venv .venv'
                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                bat '.venv\\Scripts\\python.exe -m common.report.report clean'
            }
        }

        stage('接口自动化') {
            steps {
                withEnv(["RUN_REAL=${params.RUN_REAL ? '1' : '0'}"]) {
                    bat '.venv\\Scripts\\python.exe -m pytest -m api --alluredir=reports/raw'
                }
            }
        }

        stage('Web 自动化') {
            when { expression { params.RUN_WEB } }
            steps {
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements-web.txt'
                withEnv(["RUN_REAL=${params.RUN_REAL ? '1' : '0'}"]) {
                    bat '.venv\\Scripts\\python.exe -m pytest -m web --alluredir=reports/raw'
                }
            }
        }

        stage('App 自动化（组件单测）') {
            when { expression { params.RUN_APP } }
            steps {
                bat '.venv\\Scripts\\python.exe -m pytest -m app --alluredir=reports/raw'
            }
        }
    }

    post {
        always {
            allure includeProperties: false, results: [[path: 'reports/raw']]
            archiveArtifacts artifacts: 'reports/**, logs/**', allowEmptyArchive: true
        }
    }
}
