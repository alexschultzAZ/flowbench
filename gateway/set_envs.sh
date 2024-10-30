#!/bin/bash
docker container stop kn-facerec-stateful
docker container rm kn-facerec-stateful
docker container stop kn-facextract-stateful
docker container rm kn-facextract-stateful
docker container stop kn-modect-stateful
docker container rm kn-modect-stateful
docker container stop kn-vidsplit-stateful
docker container rm kn-vidsplit-stateful


# Start the kn-facereec-local container
echo "Starting kn-facerec-stateful container..."
docker run -d --name kn-facerec-stateful -p 8083:8080 flowbench2024/kn-facerec-stateful

# Wait a few seconds to ensure the container is up
sleep 10

# Get the IP address of kn-facextract-local
FACEREC_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-facerec-stateful)
echo "kn-facerec-stateful IP: $FACEREC_IP"

# Start the kn-facextract-stateful container
echo "Starting kn-facextract-stateful container..."
docker run -d --name kn-facextract-stateful -p 8082:8080 \
  -e NEXT_URL="http://$FACEREC_IP:8080" \
  flowbench2024/kn-facextract-stateful

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-facextract-stateful
FACEXTRACT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-facextract-stateful)
echo "kn-facextract-stateful IP: $FACEXTRACT_IP"

# Start the kn-modect-stateful container and pass the NEXT_URL with the facextract IP
echo "Starting kn-modect-stateful container..."
docker run -d --name kn-modect-stateful -p 8081:8080 \
  -e NEXT_URL="http://$FACEXTRACT_IP:8080" \
  flowbench2024/kn-modect-stateful

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-modect-stateful
MODECT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-modect-stateful)
echo "kn-modect-stateful IP: $MODECT_IP"

# Start the kn-vidsplit-stateful container and pass the NEXT_URL with the modect IP
echo "Starting kn-vidsplit-stateful container..."
docker run -d --name kn-vidsplit-stateful -p 8080:8080 \
  -e NEXT_URL="http://$MODECT_IP:8080" \
  flowbench2024/kn-vidsplit-stateful

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-vidsplit-stateful
VIDSPLIT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-vidsplit-stateful)
echo "kn-vidsplit-stateful IP: $VIDSPLIT_IP"
