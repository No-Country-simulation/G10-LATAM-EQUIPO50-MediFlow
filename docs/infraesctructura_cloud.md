# Infraestructura Cloud — MediFlow (OCI)

## Región

## Cuenta y compartment
 
- Se usa la cuenta OCI Always Free ya existente
- Compartment dedicado al proyecto, separado de cualquier otro uso de la cuenta.

## Buckets (Object Storage)
 
Tres buckets segregados por estado, dentro del compartment del proyecto:
 
| Bucket | Contenido |
|---|---|
| `recibidos` | Documentos apenas ingresados, antes de procesar |
| `procesados` | Documentos con resultado del agente ya consolidado |
| `auditoria_humana` | Casos que requieren revisión humana (ambiguos o rechazados) |
 
La ruta de cada objeto dentro del bucket debe seguir la misma lógica que el campo `clasificacion.situacion` del [contrato de datos](contrato_datos.md) (Normal/Urgente/Ambiguo), para que el backend pueda escribir directo sin traducir estados.

## Acceso del equipo (IAM)
 
- La región es un atributo de los *recursos*, no de las *personas* — nadie del equipo necesita "estar" en la región para trabajar sobre los buckets o instancias de este compartimento.
- Cada compañero tiene su propio usuario en Identity & Security → Domains → Default → Users (o pertenece a un grupo con política de lectura/escritura scoped al compartment del proyecto). Al crear el usuario con su correo real, Oracle manda automáticamente la invitación para activar el acceso.
- Cada miembro del equipo tiene solo los permisos necesario sobre el compartment del proyecto.

## Despliegue (Compute)
 
Confirmado como diferencial del proyecto: la app corre en una instancia OCI Compute (Ampere A1, Always Free).
 
- Requiere una VCN — mínima: 1 subred pública + Internet Gateway + lista de seguridad abriendo solo 22 (SSH) y el puerto de la app. El asistente de creación de instancias la arma sola si no existe una.
- **IP pública reservada** (no efímera), para que la URL de la app/API no cambie si la instancia se reinicia.