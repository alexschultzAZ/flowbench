#!/bin/bash
docker container stop kn-facerec-stateless
docker container rm kn-facerec-stateless
docker container stop kn-facextract-stateless
docker container rm kn-facextract-stateless
docker container stop kn-modect-stateless
docker container rm kn-modect-stateless
docker container stop kn-vidsplit-stateless
docker container rm kn-vidsplit-stateless


# Start the kn-facereec-stateless container
echo "Starting kn-facerec-stateless container..."
docker run -d --name kn-facerec-stateless -p 8090:8080 flowbench2024/kn-facerec-stateless

# Wait a few seconds to ensure the container is up
sleep 8

# Get the IP address of kn-facextract-stateless
FACEREC_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-facerec-stateless)
echo "kn-facerec-stateless IP: $FACEREC_IP"

# Start the kn-facextract-local container
echo "Starting kn-facextract-stateless container..."
docker run -d --name kn-facextract-stateless -p 8089:8080 \
  -e NEXT_URL="http://$FACEREC_IP:8080" \
  flowbench2024/kn-facextract-stateless

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-facextract-local
FACEXTRACT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-facextract-stateless)
echo "kn-facextract-stateless IP: $FACEXTRACT_IP"

# Start the kn-modect-local container and pass the NEXT_URL with the facextract IP
echo "Starting kn-modect-stateless container..."
docker run -d --name kn-modect-stateless -p 8088:8080 \
  -e NEXT_URL="http://$FACEXTRACT_IP:8080" \
  flowbench2024/kn-modect-stateless

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-modect-stateless
MODECT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-modect-stateless)
echo "kn-modect-stateless IP: $MODECT_IP"

# Start the kn-vidsplit-local container and pass the NEXT_URL with the modect IP
echo "Starting kn-vidsplit-stateless container..."
docker run -d --name kn-vidsplit-stateless -p 8087:8080 \
  -e NEXT_URL="http://$MODECT_IP:8080" \
  flowbench2024/kn-vidsplit-stateless

# Wait a few seconds to ensure the container is up
sleep 5

# Get the IP address of kn-vidsplit-stateless
VIDSPLIT_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kn-vidsplit-stateless)
echo "kn-vidsplit-stateless IP: $VIDSPLIT_IP"
