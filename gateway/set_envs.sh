#!/bin/bash
docker container stop kn-facerec
docker container rm kn-facerec
docker container stop kn-facextract
docker container rm kn-facextract
docker container stop kn-modect
docker container rm kn-modect
docker container stop kn-vidsplit
docker container rm kn-vidsplit


# Start the kn-facereec-local container
echo "Starting kn-facerec-local container..."
docker run -d --name kn-facerec -p 8083:8080 flowbench2024/kn-facerec-local

# Wait a few seconds to ensure the container is up
sleep 10

# Get the IP address of kn-facextract-local
FACEREC_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-facerec)
echo "kn-facerec-local IP: $FACEREC_IP"

# Start the kn-facextract-local container
echo "Starting kn-facextract-local container..."
docker run -d --name kn-facextract -p 8082:8080 \
  -e NEXT_URL="http://$FACEREC_IP:8080" \
  flowbench2024/kn-facextract-local

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-facextract-local
FACEXTRACT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-facextract)
echo "kn-facextract-local IP: $FACEXTRACT_IP"

# Start the kn-modect-local container and pass the NEXT_URL with the facextract IP
echo "Starting kn-modect-local container..."
docker run -d --name kn-modect -p 8081:8080 \
  -e NEXT_URL="http://$FACEXTRACT_IP:8080" \
  flowbench2024/kn-modect-local

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-modect-local
MODECT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-modect)
echo "kn-modect-local IP: $MODECT_IP"

# Start the kn-vidsplit-local container and pass the NEXT_URL with the modect IP
echo "Starting kn-vidsplit-local container..."
docker run -d --name kn-vidsplit -p 8080:8080 \
  -e NEXT_URL="http://$MODECT_IP:8080" \
  flowbench2024/kn-vidsplit-local

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-vidsplit-local
VIDSPLIT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-vidsplit)
echo "kn-vidsplit-local IP: $VIDSPLIT_IP"
