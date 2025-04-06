#!/bin/sh
remove_containers () {
  for container in project_pyright pyright; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
      echo "Stopping and removing existing container: $container"
      docker stop $container || docker kill $container
      docker rm -f $container
    fi
  done
  
  if docker volume ls --format '{{.Name}}' | grep -q "^sources$"; then
    echo "Removing existing volume: sources"
    docker volume rm -f sources
  fi
}

lint() {
  
  # Check for exist containers and volume
  remove_containers
  
  # Run containers with sources (build_image) and node (for pyright)
  docker run -d --name project_pyright -v sources:/opt ${CI_REGISTRY}/ci_temp/${CI_PROJECT_NAME}:${CI_COMMIT_SHORT_SHA} tail -f /dev/null
  docker run -d --name pyright -w /project -v sources:/project node:23.6.0-bookworm tail -f /dev/null

  # Exec script with install pyright, complete linging and create report
  docker exec pyright bash -c "pwd && npm i -g pyright && npm i -g pyright-to-gitlab-ci && pyright --outputjson > report_raw.json; exit_code=\$?; pyright-to-gitlab-ci --src report_raw.json --output report.json --base_path .; exit \$exit_code"
  
  # Save exit code of pyright
  pyright_exit_code=$?
  
  # Move report from docker container to runner 
  docker cp pyright:/project/report.json .

  remove_containers
  
  exit $pyright_exit_code
}
$1
