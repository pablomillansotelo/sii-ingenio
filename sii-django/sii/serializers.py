from rest_framework import serializers

from sii.models import Alumno, Curso, Inscripcion, Periodo


class AlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno
        fields = [
            "id",
            "user_id",
            "nombre",
            "apellido",
            "curp",
            "email",
            "telefono",
            "fecha_nacimiento",
            "estado",
        ]
        read_only_fields = ["id"]


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ["id", "nombre", "descripcion"]
        read_only_fields = ["id"]


class PeriodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Periodo
        fields = ["id", "nombre", "fecha_inicio", "fecha_fin", "cerrado"]
        read_only_fields = ["id"]


class InscripcionSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source="alumno.nombre", read_only=True)
    curso_nombre = serializers.CharField(source="curso.nombre", read_only=True)
    periodo_nombre = serializers.CharField(source="periodo.nombre", read_only=True)

    class Meta:
        model = Inscripcion
        fields = [
            "id",
            "alumno",
            "alumno_nombre",
            "curso",
            "curso_nombre",
            "periodo",
            "periodo_nombre",
            "fecha_inscripcion",
            "intento",
            "calificacion",
            "estado",
            "puede_cursar",
        ]
        read_only_fields = ["id", "fecha_inscripcion"]
