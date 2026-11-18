pipeline {
  agent any

  triggers { githubPush() }

  options {
    disableConcurrentBuilds()
    timeout(time: 15, unit: 'MINUTES')
    timestamps()
  }

  environment {
    REG_NO    = 'FA23-BDS-014'
    IMAGE     = 'midterm-app'
    CONTAINER = 'midterm-app'
  }

  stages {

    stage('Fetch Latest Data') {
      steps {
        checkout scm
        script {
          env.GIT_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
        }
        echo "Building commit ${env.GIT_SHA}"
      }
    }

    stage('Train and Test') {
      agent {
        docker {
          image 'python:3.11-slim'
          reuseNode true
          args '-e HOME=/tmp'
        }
      }
      steps {
        sh '''
          python -m venv /tmp/venv
          . /tmp/venv/bin/activate
          pip install --no-cache-dir -r requirements.txt
          GIT_COMMIT=$GIT_SHA python train.py
          python -m pytest -q tests
        '''
      }
    }

    stage('Build Docker Image') {
      steps {
        sh 'docker build --build-arg GIT_COMMIT=$GIT_SHA -t $IMAGE:latest -t $IMAGE:${GIT_SHA} .'
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          docker rm -f $CONTAINER || true
          docker run -d --name $CONTAINER --restart unless-stopped -p 8000:8000 $IMAGE:latest
          docker image prune -f
        '''
      }
    }

    stage('Verify') {
      steps {
        sh '''
          for i in $(seq 1 30); do
            if curl -fs http://localhost:8000/metrics > metrics_out.json 2>/dev/null \
               && grep -q "$GIT_SHA" metrics_out.json; then
              echo "Verified new git_sha is live:"
              cat metrics_out.json
              exit 0
            fi
            sleep 2
          done
          echo "Verification failed: /metrics did not show $GIT_SHA"
          curl -s http://localhost:8000/metrics || true
          exit 1
        '''
      }
    }
  }

  post {
    always {
      script {
        def metrics = fileExists('metrics_out.json') ? readFile('metrics_out.json') : 'Metrics not available (build failed before verify).'
        emailext(
          from: 'harrammansoorkhan@gmail.com',
          to: 'qasimalik@gmail.com',
          cc: 'harrammansoorkhan@gmail.com',
          subject: "FA23-BDS-014 - Build ${currentBuild.currentResult} #${env.BUILD_NUMBER}",
          body: """Reg No: FA23-BDS-014
Result: ${currentBuild.currentResult}
Commit: ${env.GIT_SHA}
Build: ${env.BUILD_URL}

/metrics output:
${metrics}
"""
        )
      }
    }
  }
}
