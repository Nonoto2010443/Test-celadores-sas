#!/bin/bash
echo "🧪 Probando endpoint de generación de examen..."
echo ""

start_time=$(date +%s)
response=$(curl -s -X POST http://localhost:8001/api/exams/generate -H "Content-Type: application/json" -w "\nHTTP_CODE:%{http_code}")
end_time=$(date +%s)
duration=$((end_time - start_time))

http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
json_data=$(echo "$response" | sed '/HTTP_CODE/d')

echo "⏱️  Tiempo de respuesta: ${duration} segundos"
echo "📡 Código HTTP: $http_code"

if [ "$http_code" = "200" ]; then
    count=$(echo "$json_data" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))")
    echo "✅ Éxito: $count preguntas generadas"
    echo ""
    echo "📝 Primeras 3 preguntas:"
    echo "$json_data" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, q in enumerate(data[:3], 1):
    print(f'{i}. {q[\"texto\"][:80]}...')
"
else
    echo "❌ Error en la generación"
fi
