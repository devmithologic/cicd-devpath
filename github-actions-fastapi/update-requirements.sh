#!/bin/bash
# Script para regenerar requirements.txt desde poetry.lock

echo "🔄 Regenerating 'requirements.txt' from poetry.lock..."
poetry export -f requirements.txt --output requirements.txt --without-hashes

cat requirements.txt

echo "✅ requirements.txt updated"