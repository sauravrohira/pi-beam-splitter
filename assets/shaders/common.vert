uniform mat4 transform;
uniform mat4 modelview;
uniform mat3 normalMatrix;
uniform mat4 texMatrix;

attribute vec4 position;
attribute vec4 color;
attribute vec2 texCoord;
attribute vec3 normal;

varying vec4 vertColor;
varying vec4 vertTexCoord;
varying vec3 vertNormal;
varying vec3 vertEyeDir;

void main() {
    gl_Position = transform * position;
    vertColor = color;
    vertTexCoord = texMatrix * vec4(texCoord, 1.0, 1.0);
    vertNormal = normalize(normalMatrix * normal);
    // Eye direction in camera space — camera sits at origin so direction is -position
    vec3 vertPos = vec3(modelview * position);
    vertEyeDir = normalize(-vertPos);
}
