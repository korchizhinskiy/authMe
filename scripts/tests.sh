#!/bin/sh

test() {
  
  # Check for exist containers
  for container in project_test; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
      echo "Stopping and removing existing container: $container"
      docker stop $container && docker rm $container
    fi
  done

  # Run containers with sources (build_image)
  docker run -d --name project_test -w /opt -v /var/run/docker.sock:/var/run/docker.sock ${CI_REGISTRY}/ci_temp/${CI_PROJECT_NAME}:${CI_COMMIT_SHORT_SHA} tail -f /dev/null

  # Run pytest with coverage output
  docker exec project_test bash -c "pytest --junit-xml=report.xml --cov --cov-report term --cov-report=html:coverage-report --cov-report=xml:coverage.xml --cov-branch"
  
  # Save exit code of pytest
  pytest_exit_code=$?
  
  # Move report from docker container to runner 
  docker cp project_test:/opt/report.xml .
  docker cp project_test:/opt/coverage.xml .

  # Stop and remove container
  docker stop project_test
  docker rm project_test
  
  exit $pytest_exit_code
}
$1
