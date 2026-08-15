# Guía de usuario: facturación de recepciones de compra

## Finalidad de la nueva funcionalidad

Esta funcionalidad permite crear facturas de proveedor a partir de los
albaranes de recepción que el usuario seleccione.

De este modo, ya no es necesario facturar todo lo que esté pendiente en una
orden de compra. Cada factura incluirá únicamente las cantidades recibidas en
los albaranes elegidos en ese momento.

La factura se crea inicialmente en estado **Borrador**, para que pueda ser
revisada antes de validarla.

## ¿Qué cambia para el usuario?

Hasta ahora, al crear una factura desde una orden de compra, Odoo podía añadir
todas las cantidades recibidas y pendientes de facturar de esa orden.

Con la nueva opción, el usuario comienza el proceso desde la lista de
recepciones y decide exactamente qué albaranes quiere facturar. Las demás
recepciones pendientes no se añaden a la factura y quedan disponibles para
facturarlas más adelante.

## Cómo crear las facturas

1. Acceder a **Inventario > Operaciones > Transferencias**.
2. Localizar las recepciones de proveedor que se desean facturar. Puede
   utilizarse el filtro **Recepciones de compra a facturar** para encontrarlas
   con mayor facilidad.
3. Marcar una o varias recepciones en la lista.
4. Abrir el menú **Acción** y seleccionar **Crear facturas de proveedor desde
   recepciones**.
5. Revisar los albaranes mostrados en la ventana de confirmación.
6. Elegir el tipo de agrupación.
7. Pulsar **Crear facturas de proveedor**.

Al finalizar:

- Si se crea una sola factura, Odoo abrirá directamente su formulario.
- Si se crean varias facturas, Odoo mostrará la lista de facturas generadas.
- Todas las facturas quedarán en **Borrador** para su comprobación y
  validación posterior.

## Opciones de agrupación

### Factura compatible por proveedor

Es la opción recomendada cuando se desea agrupar varias recepciones.

Odoo reunirá en una misma factura los albaranes que tengan condiciones
compatibles. Por ejemplo, deben coincidir el proveedor, la empresa, la moneda,
las condiciones de pago y la configuración fiscal.

Los albaranes pueden pertenecer a órdenes de compra diferentes. Si las
condiciones no coinciden, Odoo creará automáticamente facturas separadas.

Por tanto, si se seleccionan albaranes de proveedores distintos, no se
mezclarán en una única factura: se generará una factura independiente para
cada proveedor y conjunto de condiciones compatibles.

### Una factura por recepción

Esta opción crea una factura independiente para cada albarán seleccionado,
aunque varios albaranes sean del mismo proveedor y pudieran agruparse.

Es útil cuando el proveedor envía una factura distinta por cada recepción o
cuando la empresa desea mantener cada albarán separado.

## Ejemplo práctico

Existen las siguientes recepciones pendientes:

| Orden de compra | Recepción | Cantidad |
| --- | --- | ---: |
| PC00001 | Albarán 1 | 10 unidades |
| PC00001 | Albarán 2 | 20 unidades |
| PC00001 | Albarán 3 | 15 unidades |
| PC00002 | Albarán 4 | 8 unidades |
| PC00002 | Albarán 5 | 12 unidades |

El usuario selecciona el Albarán 1, el Albarán 3 y el Albarán 4.

Si las dos órdenes corresponden al mismo proveedor y sus condiciones son
compatibles, se creará una factura que contendrá exclusivamente:

- 10 unidades del Albarán 1.
- 15 unidades del Albarán 3.
- 8 unidades del Albarán 4.

El Albarán 2 y el Albarán 5 no aparecerán en esa factura y continuarán
pendientes para un proceso posterior.

## Condiciones que deben cumplir las recepciones

Para poder utilizar esta opción:

- El albarán debe ser una recepción procedente de un proveedor.
- La recepción debe estar terminada y validada.
- Los productos recibidos deben proceder de una orden de compra.
- Las cantidades deben seguir pendientes de facturación.
- El proveedor no debe estar bloqueado para facturación, si la empresa utiliza
  ese control.

Si alguna recepción no cumple estas condiciones, Odoo mostrará un mensaje y
no creará una factura incorrecta.

## Control para evitar duplicidades

Una recepción que ya esté vinculada a una factura activa no podrá volver a
facturarse mediante esta opción. Este control evita que dos usuarios facturen
el mismo albarán por error.

Si otro usuario está procesando simultáneamente una de las recepciones
seleccionadas, Odoo solicitará intentarlo de nuevo cuando termine esa
operación.

Si la factura se cancela o elimina, la recepción podrá volver a quedar
disponible para facturación, siempre que continúe existiendo cantidad pendiente.

## Consulta y trazabilidad

En la lista y en el formulario del albarán se muestra su estado de facturación:

- **Pendiente de facturar**: todavía no se ha facturado la recepción.
- **Facturado parcialmente**: solo parte de sus movimientos está facturada.
- **Facturado**: toda la recepción está facturada.
- **No aplicable**: el documento no reúne las condiciones para este proceso.

Desde el albarán también puede abrirse la factura o las facturas relacionadas.
En cada línea de factura se muestra la recepción de la que procede. Asimismo,
se mantiene la relación con la orden de compra original.

Esto permite consultar el recorrido completo:

**Factura de proveedor → orden de compra → recepción → productos recibidos.**

## Revisión de la factura

Antes de validar la factura se recomienda comprobar:

- El proveedor.
- La fecha de factura.
- Las órdenes de compra indicadas como origen.
- Los albaranes mostrados en las líneas.
- Las cantidades y precios.
- Los impuestos y condiciones de pago.

Las cantidades y unidades de las líneas creadas desde una recepción quedan
protegidas para conservar la trazabilidad y evitar diferencias con el albarán.
Si se ha seleccionado una recepción equivocada, debe eliminarse o cancelarse
la factura en borrador y repetir el proceso con los albaranes correctos.

## Preguntas frecuentes

### ¿Puedo seleccionar albaranes de órdenes de compra diferentes?

Sí. Pueden agruparse en una misma factura si pertenecen al mismo proveedor y
el resto de sus condiciones son compatibles.

### ¿Qué ocurre si selecciono albaranes de proveedores distintos?

Odoo crea facturas separadas. Nunca mezcla varios proveedores en la misma
factura.

### ¿Se facturarán otros albaranes pendientes de las órdenes seleccionadas?

No. Solo se incluirán los albaranes marcados por el usuario.

### ¿Puedo facturar más adelante las recepciones que no seleccione?

Sí. Continuarán pendientes y podrán seleccionarse en otro proceso de
facturación.

### ¿La factura queda validada automáticamente?

No. Se crea en estado Borrador para que el usuario pueda revisarla antes de
validarla.

### ¿Sustituye esta opción a la facturación desde la orden de compra?

No. El proceso habitual desde la orden de compra continúa disponible. La nueva
opción debe utilizarse cuando sea necesario elegir recepciones concretas.

### ¿Se pueden incluir recepciones todavía no terminadas?

No. Primero deben validarse y quedar en estado Terminado.

## Recomendación de uso

Cuando una orden de compra tenga varias entregas y estas deban facturarse en
momentos diferentes, se recomienda crear la factura desde las recepciones en
lugar de hacerlo desde la orden de compra.
