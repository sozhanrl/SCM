# SCM Jenkins deployment

Jenkins: http://localhost:8081
Job: SCM-Docker-Deploy
Application: http://localhost:5000

The configured Jenkins job uses an inline copy of Jenkinsfile and checks out
https://github.com/sozhanrl/SCM.git, branch main. Git polling is H/5 * * * *.
After changing Jenkinsfile, update the job's Pipeline script in Jenkins; this
local file does not automatically change the configured inline pipeline.

Stages: Checkout -> Docker build -> pytest -> Deploy. Tests execute in a
separate container without deployment data mounted. JUnit XML is published even
when pytest fails. A test failure or unstable test report prevents deployment.
The deployed image is the image tested by that build. Deployment checks HTTP
and retains the previous app container for rollback.

Persistent volumes:
- jenkins_home: existing Jenkins accounts, settings, credentials and jobs
- scm_database: /app/instance (SQLite database)
- scm_uploads: /app/uploads

The existing E:\SCM database and uploads were copied into the application
volumes. Builds never seed or reset these volumes. Runtime environment values
are stored privately at /var/jenkins_home/scm-runtime.env (mode 600), outside
the repository and application image.

Jenkins image: scm-jenkins:docker, built from Dockerfile.jenkins.
Jenkins runs as the existing jenkins user with the Docker socket group added.
The original stopped container is jenkins-before-docker-cli. Do not run both
Jenkins containers at the same time: they share jenkins_home.

Docker's data disk was moved to:
D:\DockerDesktop\wsl\disk\docker_data.vhdx
A byte-verified pre-recovery backup is retained at:
D:\Docker-Recovery-20261020\docker_data.vhdx

Do not delete volumes or factory-reset Docker to redeploy the application.
Use Build Now on the existing Jenkins job.
