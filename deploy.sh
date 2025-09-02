#!/bin/bash

echo "🚀 DÉPLOIEMENT OLLAMA PHI3:MINI ULTRA-RAPIDE"

# Arrêter les anciens containers
echo "🛑 Arrêt containers existants..."
docker stop ollama-phi3-ultra 2>/dev/null || true
docker rm ollama-phi3-ultra 2>/dev/null || true

# Démarrage (sans build)
echo "🔨 Démarrage container Phi3..."
docker-compose -f docker-compose-phi3.yml up -d

echo "⏳ Téléchargement Phi3:mini en cours..."
echo "📊 Suivre les logs: docker logs -f ollama-phi3-ultra"

# Attendre le téléchargement
sleep 90

# Test
echo "🧪 Test de connexion..."
if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "phi3"; then
    echo "✅ Phi3:mini opérationnel"
else
    echo "⏳ Encore en téléchargement, vérifiez:"
    echo "   docker logs ollama-phi3-ultra"
fi

echo "🎯 Déploiement terminé!"