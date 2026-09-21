var vents = {
    items: {
        id_cliente: '',
        fecha: '',
        products: []
    },
    add: function (item) {
        this.items.products.push(item);
        this.list();
    },
    list: function () {
        $('#tblProducts').DataTable({
            responsive: true,
            autoWidth: false,
            destroy: true,
            data: this.items.products,
            columns: [
                {"data": "id_producto"},
                {"data": "cantidad"},
                {"data": "descuento"},
                {"data": "opciones"},
            ],
            columnDefs: [

                {
                    targets: [0],
                    class: 'text-center',
                    orderable: false,
                    render: function (data, type, row) {
                        return  ''+row.id_producto;
                    }
                },
                {
                    targets: [1],
                    class: 'text-center',
                    orderable: false,
                    render: function (data, type, row) {
                        return ''+row.cantidad;
                    }
                },
                {
                    targets: [2],
                    class: 'text-center',
                    orderable: false,
                    render: function (data, type, row) {
                        return '$$' +row.descuento;
                    }
                },
                {
                    targets: [3],
                    class: 'text-center',
                    orderable: false,
                    render: function (data, type, row) {
                        return '<a rel="remove" class="btn btn-danger btn-xs btn-flat"><i class="fas fa-trash-alt"></i></a>';
                    }
                },
            ],
            initComplete: function (settings, json) {

            }
        });
    },
};

$(function () {
    $().select2({
       theme: "bootstrap",
       language: 'es'
    });
    $('#date_joined').datetimepicker()
});

function agregar_productos(){
    var producto = {
        id_producto: document.getElementById("id_producto_add").value,
        cantidad: document.getElementById("cantidad_add").value,
        descuento: document.getElementById("descuento_add").value
    };
    vents.add(producto);
}

function pagar_carrito(){
    var nplainArray = [];
    var plainArray = vents.items.products;
    for (var i = 0; i < plainArray.length; i++) {
        aux = []
        aux.push(plainArray[i].id_producto.toString());
        aux.push(plainArray[i].cantidad.toString());
        aux.push(plainArray[i].descuento.toString());
        nplainArray.push(aux);
    }


    vents.items.id_cliente = document.getElementById("id_cliente_add").value;
    vents.items.fecha = document.getElementById("fecha_add").value;

    var parameters = new FormData();
    parameters.appened('vents', vents.items);

    $.ajax({
        type: 'POST',
        url: 'add_carrito/',
        data: parameters,
        dataType: 'json',
        processData: false,
        contentType: false,
    });
}

