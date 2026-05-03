#ifdef GL_ES
precision mediump float;
#endif

uniform sampler2D texture;
uniform vec2 texOffset;
uniform float density;
uniform float strength;

void main() {
    vec2 uv = gl_FragCoord.xy * texOffset;
    vec4 texColor = texture2D(texture, uv);

    float line     = sin(uv.y * density * 3.14159) * 0.5 + 0.5;
    float scanline = 1.0 - strength * (1.0 - line);

    gl_FragColor = vec4(texColor.rgb * scanline, texColor.a);
}
