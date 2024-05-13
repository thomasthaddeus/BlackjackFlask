#!/bin/bash

# Define the path to the directory containing the Dockerfiles
DOCKERFILES_DIR=".docker"

# Change to the directory with Dockerfiles
cd $DOCKERFILES_DIR

# Loop through each Dockerfile in the directory
for dockerfile in Dockerfile.*; do
    # Extract the environment type from the Dockerfile name (e.g., "dev" from "Dockerfile.dev")
    env_type=$(echo $dockerfile | sed 's/Dockerfile.//')

    # Define image and container names based on the environment type
    image_name="myapp-$env_type"
    container_name="myapp-$env_type-container"

    # Build the Docker image
    echo "Building Docker image for $env_type environment..."
    docker build -f $dockerfile -t $image_name .

    # Check if we should run the container immediately
    # Optionally, handle different run commands based on the environment type
    if [ "$env_type" = "dev" ]; then
        echo "Running container for $env_type environment..."
        docker run -d -p 5000:5000 --name $container_name $image_name
    elif [ "$env_type" = "test" ]; then
        echo "Running tests in the $env_type environment..."
        docker run --name $container_name $image_name
    fi

    echo "Operation for $env_type environment completed."
    echo
done

# Return to the original directory
cd -
