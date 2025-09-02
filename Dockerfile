# Dockerfile.ollama-phi3
FROM ollama/ollama:latest

# Variables d'environnement pour optimisation maximale
ENV OLLAMA_FLASH_ATTENTION=1
ENV OLLAMA_KV_CACHE_TYPE=q4_0
ENV OLLAMA_NUM_PARALLEL=1
ENV OLLAMA_MAX_LOADED_MODELS=1
ENV OLLAMA_NUM_CTX=1024

# Exposition du port
EXPOSE 11434

# Script d'initialisation pour télécharger automatiquement phi3:mini
RUN echo '#!/bin/bash\n\
ollama serve &\n\
sleep 10\n\
ollama pull phi3:mini\n\
echo "✅ Phi3:mini téléchargé et optimisé"\n\
wait' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
