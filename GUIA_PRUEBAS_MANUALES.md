# 🧪 GUÍA DE PRUEBAS MANUALES COMPLETA
## Preparación Oposiciones SAS - Celadores

**Fecha:** 15 de Octubre de 2025  
**Versión:** 4.0 - Todas las funcionalidades implementadas  
**URL de Pruebas:** https://healthcare-tests.preview.emergentagent.com

---

## 📋 CHECKLIST COMPLETO DE CAMBIOS A VERIFICAR

### ✅ **1. COMPOSICIÓN DEL EXAMEN (95% BD / 5% IA)**
- [ ] El examen tiene exactamente 50 preguntas
- [ ] Aproximadamente 47-48 preguntas de la base de datos
- [ ] Aproximadamente 2-3 preguntas generadas por IA
- [ ] Distribución: 30% Temario Común (15 preguntas)
- [ ] Distribución: 70% Temario Específico (35 preguntas)

### ✅ **2. DISTRIBUCIÓN EQUITATIVA DE TEMAS**
- [ ] Preguntas distribuidas entre múltiples temas
- [ ] Temario Común (T1-T10): 1-2 preguntas por tema
- [ ] Temario Específico (T11-T19): 3-4 preguntas por tema
- [ ] NO hay concentración excesiva (ej: 10 preguntas del mismo tema)

### ✅ **3. FORMATO OFICIAL DE LEYES**
- [ ] Las leyes aparecen con número, fecha y nombre completo
- [ ] Ejemplo correcto: "Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales"
- [ ] NO aparecen nombres simples: "Ley de Prevención de Riesgos Laborales"
- [ ] Constitución aparece como: "Constitución Española de 1978"
- [ ] Estatuto de Autonomía: "Ley Orgánica 2/2007, de 19 de marzo..."

### ✅ **4. CALIDAD GRAMATICAL Y ORTOGRÁFICA**
- [ ] NO hay errores como "AutonomíaA"
- [ ] NO hay dobles espacios
- [ ] NO hay espacios antes de puntuación
- [ ] Acentuación correcta en todas las palabras

### ✅ **5. PROHIBICIÓN DE ABREVIATURAS**
- [ ] NO aparece LOPDPGDD (debe ser nombre completo con fecha)
- [ ] NO aparece LPRL (debe ser Ley 31/1995...)
- [ ] NO aparece EM (debe ser Ley 55/2003...)
- [ ] NO aparece EA (debe ser Ley Orgánica 2/2007...)
- [ ] SÍ aparece "SAS" (única abreviatura permitida)

### ✅ **6. JUSTIFICACIONES DINÁMICAS CON IA**
- [ ] Cada pregunta tiene justificación detallada
- [ ] Primer párrafo explica por qué la correcta es correcta
- [ ] Párrafos siguientes analizan cada opción incorrecta
- [ ] Total: 4-6 párrafos por justificación
- [ ] Tono profesional y didáctico
- [ ] Referencias a leyes específicas
- [ ] Extensión: ~200-400 palabras por justificación

### ✅ **7. SISTEMA DE PUNTUACIÓN**
- [ ] Pregunta correcta: +2 puntos
- [ ] Pregunta incorrecta: -0.5 puntos
- [ ] Pregunta en blanco: 0 puntos
- [ ] Puntuación mínima: 0 (no negativa)
- [ ] Mensaje de éxito si ≥65 puntos

---

## 🚀 INSTRUCCIONES PASO A PASO PARA PRUEBAS

### **PASO 1: ACCESO A LA APLICACIÓN**

1. **Abre tu navegador** (Chrome, Firefox, Safari, Edge)
2. **Accede a:** https://healthcare-tests.preview.emergentagent.com
3. **Verifica que la página carga correctamente**

---

### **PASO 2: INICIO DE SESIÓN**

**Si ya tienes cuenta:**
1. Haz clic en "Iniciar Sesión" o "Login"
2. Introduce tu email y contraseña
3. Haz clic en "Entrar"

**Si NO tienes cuenta:**
1. Haz clic en "Registrarse" o "Register"
2. Completa el formulario:
   - Nombre completo
   - Email
   - Contraseña
3. Haz clic en "Registrarse"
4. Inicia sesión con tus credenciales

**⚠️ Nota sobre Suscripción:**
Si no tienes suscripción activa, puedes:
- Probar el flujo de suscripción (Stripe test mode)
- O solicitar que active manualmente tu suscripción para pruebas

---

### **PASO 3: GENERAR NUEVO EXAMEN**

1. **Dashboard:** Deberías ver el Dashboard personal
2. **Busca el botón:** "Comenzar Nuevo Examen" o "Generate New Exam"
3. **Haz clic** en el botón
4. **Espera:** La generación puede tomar 5-10 segundos

**✅ Verificar:**
- ✓ El examen se genera sin errores
- ✓ Aparecen exactamente 50 preguntas
- ✓ Timer de 90 minutos comienza

---

### **PASO 4: REVISAR CALIDAD DE LAS PREGUNTAS**

**Durante el examen, revisa las primeras 10-15 preguntas:**

**4.1 Formato Oficial de Leyes**
- [ ] Busca preguntas que mencionen leyes
- [ ] Verifica formato: "Ley X/YYYY, de DD de mes, de..."
- [ ] Ejemplo esperado: "Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos Laborales"
- [ ] NO debe aparecer: "Ley de Prevención de Riesgos Laborales" (sin fecha)

**4.2 Abreviaturas Prohibidas**
- [ ] Busca y verifica que NO aparezcan:
  - LOPDPGDD
  - LPRL
  - EM, EMPNS
  - EA, EAA
  - BOE, BOJA
  - RD
- [ ] Verifica que SÍ aparezca: "SAS" (única permitida)

**4.3 Calidad Gramatical**
- [ ] Lee varias preguntas completas
- [ ] Verifica que NO haya:
  - "AutonomíaA" o similares
  - Dobles espacios "  "
  - Espacios antes de puntos " ."
  - Errores de acentuación

**4.4 Estructura de Preguntas**
- [ ] Todas las preguntas comienzan con "❓FFM.-"
- [ ] Cada pregunta tiene exactamente 4 opciones (A, B, C, D)
- [ ] Las opciones son claras y no están vacías

---

### **PASO 5: VERIFICAR DISTRIBUCIÓN DE TEMAS**

**Mientras respondes el examen:**

1. **Observa los temas** de las preguntas (si se muestran)
2. **Anota mentalmente** la variedad de temas
3. **Verifica que NO haya:**
   - 10+ preguntas del mismo tema
   - Concentración excesiva en 2-3 temas
4. **Verifica que SÍ haya:**
   - Preguntas de múltiples temas diferentes
   - Distribución equilibrada

---

### **PASO 6: COMPLETAR EL EXAMEN**

**Opciones para pruebas rápidas:**

**Opción A: Respuesta Rápida**
- Responde todas las preguntas rápidamente
- Puedes responder al azar para acelerar
- Objetivo: Llegar a la pantalla de resultados

**Opción B: Respuesta Parcial**
- Responde solo las primeras 20-30 preguntas
- Deja algunas en blanco
- Objetivo: Verificar cálculo de puntuación

**Opción C: Respuesta Mixta (Recomendado)**
- Responde 15-20 correctas (si las conoces)
- Responde 5-10 incorrectas intencionalmente
- Deja 5-10 en blanco
- Objetivo: Verificar cálculo completo (+2/-0.5/0)

**Finalmente:**
1. **Haz clic en "Enviar Examen"** o "Submit Exam"
2. **Confirma** el envío si aparece diálogo
3. **ESPERA 2.5-4 MINUTOS** (generación de justificaciones con IA)

**⏱️ IMPORTANTE:** La generación de justificaciones toma tiempo porque el sistema está generando 50 justificaciones detalladas con IA. Ten paciencia.

---

### **PASO 7: VERIFICAR PANTALLA DE RESULTADOS**

**7.1 Verificar Puntuación**
- [ ] Aparece la puntuación total (sobre 100)
- [ ] Aparece número de correctas
- [ ] Aparece número de incorrectas
- [ ] Aparece número de en blanco
- [ ] Cálculo correcto: (correctas × 2) - (incorrectas × 0.5) = puntuación
- [ ] Puntuación mínima es 0 (nunca negativa)
- [ ] Si puntuación ≥ 65, aparece mensaje de éxito

**7.2 Verificar Justificaciones Detalladas (CRÍTICO)**

Para 5-10 preguntas, verifica que cada justificación tenga:

**Estructura:**
- [ ] **Primer párrafo:** Explica por qué la opción correcta es correcta
- [ ] **Segundo párrafo:** Analiza la primera opción incorrecta
- [ ] **Tercer párrafo:** Analiza la segunda opción incorrecta
- [ ] **Cuarto párrafo:** Analiza la tercera opción incorrecta
- [ ] Total: 4-6 párrafos

**Contenido:**
- [ ] **Referencias legales:** Menciona leyes específicas (Ley 31/1995, artículos, etc.)
- [ ] **Tono profesional:** Lenguaje formal y didáctico
- [ ] **Análisis individual:** Cada opción incorrecta explicada por separado
- [ ] **Extensión:** Cada justificación tiene ~200-400 palabras

**Calidad:**
- [ ] Explicaciones claras y comprensibles
- [ ] No son genéricas ni vagas
- [ ] Proporcionan valor educativo real
- [ ] En español correcto

**Ejemplo de lo que deberías ver:**

```
Párrafo 1:
La respuesta correcta es la opción B porque refleja fielmente 
la definición oficial establecida en el artículo 4 de la 
Ley 31/1995, de 8 de noviembre, de Prevención de Riesgos 
Laborales. Este artículo define el "equipo de protección 
individual" (EPI) como cualquier equipo destinado...

Párrafo 2:
La opción A es incorrecta porque presenta una definición 
incompleta que omite el elemento esencial: la finalidad 
protectora. Si bien es cierto que un EPI debe ser "llevado 
o sujetado por el trabajador"...

Párrafo 3:
La opción C es incorrecta por ser excesivamente vaga e 
imprecisa. La expresión "cualquier equipo que el trabajador 
pueda llevar consigo" es tan amplia que podría incluir...

Párrafo 4:
La opción D es claramente incorrecta y no representa ninguna 
definición válida o útil desde el punto de vista legal...
```

---

### **PASO 8: VERIFICAR HISTORIAL**

1. **Vuelve al Dashboard**
2. **Busca la sección de "Historial" o "History"**
3. **Verifica que aparece:**
   - [ ] El examen recién completado
   - [ ] Fecha y hora correctas
   - [ ] Puntuación correcta
   - [ ] Opción de ver resultados detallados

---

## 📊 REGISTRO DE PRUEBAS

### **RESULTADOS DE TU PRUEBA**

**Fecha de prueba:** _______________

**1. COMPOSICIÓN DEL EXAMEN**
- Total preguntas: ______ (debe ser 50)
- Preguntas DB: ______ (debe ser ~47-48)
- Preguntas IA: ______ (debe ser ~2-3)
- ✅ Correcto  ❌ Incorrecto

**2. DISTRIBUCIÓN DE TEMAS**
- Temas diferentes observados: ______
- ¿Distribución equilibrada? ✅ Sí  ❌ No
- ¿Concentración excesiva? ✅ No  ❌ Sí

**3. FORMATO OFICIAL DE LEYES**
- ¿Leyes con número y fecha? ✅ Sí  ❌ No
- ¿Encontraste nombres sin fecha? ✅ No  ❌ Sí
- Ejemplo encontrado: _________________________

**4. CALIDAD GRAMATICAL**
- ¿Errores tipo "AutonomíaA"? ✅ No  ❌ Sí
- ¿Dobles espacios? ✅ No  ❌ Sí
- ¿Calidad general? ✅ Excelente  ⚠️ Aceptable  ❌ Pobre

**5. ABREVIATURAS PROHIBIDAS**
- ¿Encontraste LOPDPGDD? ✅ No  ❌ Sí
- ¿Encontraste LPRL? ✅ No  ❌ Sí
- ¿Encontraste EM? ✅ No  ❌ Sí
- ¿Encontraste otras prohibidas? ✅ No  ❌ Sí
- ¿Encontraste "SAS"? ✅ Sí  ❌ No (debe estar)

**6. JUSTIFICACIONES CON IA**
- ¿Tiempo de espera? ______ minutos (esperado: 2.5-4)
- ¿Justificaciones generadas? ✅ Sí  ❌ No
- ¿Formato multi-párrafo (4-6)? ✅ Sí  ❌ No
- ¿Análisis individual de incorrectas? ✅ Sí  ❌ No
- ¿Referencias a leyes específicas? ✅ Sí  ❌ No
- ¿Tono profesional/didáctico? ✅ Sí  ❌ No
- ¿Extensión adecuada (200-400 palabras)? ✅ Sí  ❌ No
- Calidad general: ✅ Excelente  ⚠️ Buena  ❌ Pobre

**7. PUNTUACIÓN**
- Correctas: ______ × 2 = ______
- Incorrectas: ______ × (-0.5) = ______
- En blanco: ______ × 0 = ______
- Puntuación total: ______
- ¿Cálculo correcto? ✅ Sí  ❌ No
- ¿Puntuación ≥ 0? ✅ Sí  ❌ No

---

## 🐛 REPORTE DE PROBLEMAS

**Si encuentras algún problema, anota:**

**Problema 1:**
- Descripción: _________________________________
- Paso donde ocurrió: _________________________
- Captura de pantalla: ________________________

**Problema 2:**
- Descripción: _________________________________
- Paso donde ocurrió: _________________________
- Captura de pantalla: ________________________

**Problema 3:**
- Descripción: _________________________________
- Paso donde ocurrió: _________________________
- Captura de pantalla: ________________________

---

## ✅ RESUMEN FINAL

**¿Todas las funcionalidades funcionan correctamente?**
- [ ] Sí, todo funciona perfectamente
- [ ] Sí, con problemas menores
- [ ] No, hay problemas importantes

**Calificación general de la aplicación:**
⭐⭐⭐⭐⭐ (1-5 estrellas): ______

**Comentarios adicionales:**
_________________________________________________
_________________________________________________
_________________________________________________

---

## 📞 SOPORTE

Si encuentras algún problema o tienes preguntas durante las pruebas, puedes:
1. Tomar capturas de pantalla del problema
2. Anotar los pasos exactos para reproducirlo
3. Compartir esta información para resolución

---

**¡Gracias por probar la aplicación! Tus comentarios son invaluables para asegurar la calidad del producto final.** 🚀
