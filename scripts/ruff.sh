#!/bin/sh
remove_containers () {
  for container in ruff; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
      echo "Stopping and removing existing container: $container"
      docker stop $container || docker kill $container
      docker rm -f $container
    fi
  done
}

lint() {
  
  # Check for exist containers and volume
  remove_containers
  
  # Run containers with sources (build_image)
  docker run -d --name ruff ${CI_REGISTRY}/ci_temp/${CI_PROJECT_NAME}:${CI_COMMIT_SHORT_SHA} tail -f /dev/null

  # Exec script with install pyright, complete linging and create report
  docker exec ruff bash -c "ruff check --output-format=gitlab > ruff_report.json; exit_code=\$?; exit \$exit_code"
  
  # Save exit code of ruff
  ruff_exit_code=$?
  
  # Move report from docker container to runner 
  docker cp ruff:/opt/ruff_report.json .

  remove_containers
  
  exit $ruff_exit_code
}
$1
