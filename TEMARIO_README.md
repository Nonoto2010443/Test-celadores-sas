# 📚 Temario Completo de Celadores SAS

## 📊 Resumen del Contenido

Este proyecto contiene el **temario oficial completo** para las oposiciones de Celadores del Servicio Andaluz de Salud (SAS).

### 📁 Archivos del Temario

**Ubicación:** `/app/data/temario/`

1. **`temario_comun_t1-t10.pdf`**
   - Tamaño: 80 MB
   - Páginas: 743
   - Contenido: Temas 1-10 (Temario Común)

2. **`temario_especifico_t11-t19.pdf`**
   - Tamaño: 193 MB
   - Páginas: 821
   - Contenido: Temas 11-19 (Temario Específico)

**Total:** 273 MB | 1,564 páginas

---

## 📖 Estructura del Temario

### TEMARIO COMÚN (Temas 1-10)

1. **La Constitución Española de 1978**
   - Valores superiores y principios inspiradores
   - Derechos y deberes fundamentales
   - Jefatura del Estado y Poderes Públicos
   - Derecho a la protección de la salud

2. **Estatuto de Autonomía de Andalucía**
   - Ley Orgánica 2/2007, de 19 de marzo
   - Derechos sociales, deberes y políticas públicas
   - Competencias en materia de salud, sanidad y farmacia

3. **Organización sanitaria (I) - Ley General de Sanidad**
   - Ley 14/1986, de 25 de abril
   - Principios generales del sistema de salud
   - Estructura del sistema sanitario público
   - Ley 2/1998 de Salud de Andalucía

4. **Organización sanitaria (II) - SAS y Áreas de Gestión**
   - Consejería competente en materia de salud
   - Servicio Andaluz de Salud
   - Atención Primaria y Especializada
   - Áreas de organización especial

5. **LOPD y Transparencia Pública**
   - Ley Orgánica 3/2018 de Protección de Datos
   - Principios de protección de datos
   - Ley 1/2014 de Transparencia Pública de Andalucía

6. **Prevención de Riesgos Laborales**
   - Ley 31/1995, de 8 de noviembre
   - Derechos y obligaciones
   - Organización en el SAS

7. **Igualdad de género y violencia de género**
   - Ley 12/2007 para la promoción de la igualdad
   - Ley 13/2007 de prevención de violencia de género
   - Plan de Igualdad de la Junta de Andalucía

8. **Estatuto Marco del personal estatutario**
   - Ley 55/2003, de 16 de diciembre
   - Clasificación del personal
   - Derechos y deberes
   - Carrera profesional y retribuciones

9. **Autonomía del paciente y documentación clínica**
   - Ley 41/2002, de 14 de noviembre
   - Derecho de información sanitaria
   - Consentimiento informado
   - Historia clínica

10. **Tecnologías de la información en el SAS**
    - Sistemas de información corporativos
    - Puesto de trabajo digital
    - Ciberseguridad

### TEMARIO ESPECÍFICO (Temas 11-19)

11. **Visión general del Celador como profesional sanitario**
    - El trabajo en equipo
    - Integración en los equipos del SAS

12. **Habilidades sociales y comunicación**
    - El ciudadano como centro del sistema
    - La comunicación como herramienta
    - Estilos de comunicación

13. **El Celador en Hospitalización, Quirófano y Urgencias**
    - Unidades de Hospitalización
    - Bloque Quirúrgico
    - Unidades de Cuidados Críticos

14. **El Celador en Consultas Externas y otras unidades**
    - Área de Consultas Externas
    - Suministros y Almacenes
    - Farmacia y Salud Mental

15. **Movilización y traslado de pacientes**
    - Técnicas de movilización
    - Traslado en camilla y silla de ruedas
    - Posiciones anatómicas básicas
    - Actuaciones con pacientes fallecidos

16. **Manual de Estilo del SAS**
    - Valores y principios del SAS
    - Características de la atención
    - Organización de la atención sanitaria

17. **Prevención de riesgos laborales específica de Celadores**
    - Riesgos en seguridad
    - Riesgos ergonómicos y psicosociales
    - Prevención de agresiones

18. **Plan de autoprotección y emergencias**
    - Plan de Emergencias ante incendios
    - Medidas preventivas
    - Equipos de Primera Intervención (EPI)

19. **Política Ambiental del SAS y gestión de residuos**
    - Impactos ambientales
    - Gestión de residuos en centros sanitarios
    - Clasificación y segregación

---

## 💾 Base de Datos MongoDB

### Colección: `temario`

Los 19 temas están almacenados en MongoDB con la siguiente estructura:

```javascript
{
  "numero": 1,
  "titulo": "La Constitución Española de 1978",
  "tipo": "común",  // o "específico"
  "archivo": "temario_comun_t1-t10.pdf",
  "fecha_importacion": ISODate("2025-10-15T14:22:00Z"),
  "pdf_path": "/app/data/temario/temario_comun_t1-t10.pdf",
  "paginas_totales": 743,
  "contenido_disponible": true
}
```

### Comandos útiles

**Ver todos los temas:**
```bash
python3 backend/process_temario.py
```

**Consultar MongoDB:**
```bash
mongosh test_database --eval "db.temario.find({}, {numero:1, titulo:1, tipo:1})"
```

---

## 🤖 Uso en la Aplicación

La aplicación utiliza este temario completo para:

1. **Generar preguntas con IA** basadas en el contenido real de los 19 temas
2. **Proporcionar contexto** a las preguntas generadas
3. **Validar respuestas** con información oficial
4. **Ofrecer explicaciones** basadas en el temario oficial

---

## 📅 Información del Temario

- **Curso:** 2024-2025
- **Tipo:** OCR (texto extraíble)
- **Formato:** PDF
- **Total páginas:** 1,564
- **Peso total:** 273 MB
- **Fecha de importación:** 15 de Octubre de 2025

---

## ⚙️ Procesamiento

El temario ha sido procesado y almacenado mediante:

- Script: `backend/process_temario.py`
- Base de datos: MongoDB (`test_database`)
- Colección: `temario`
- Estado: ✅ **19 temas almacenados correctamente**

---

## 🔐 Nota Importante

Este material es para uso exclusivo de estudio personal para las oposiciones de Celadores del SAS. Todos los derechos reservados a sus respectivos autores y al Servicio Andaluz de Salud.
