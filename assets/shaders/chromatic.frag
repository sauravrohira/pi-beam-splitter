#ifdef GL_ES
precision mediump float;
#endif

uniform sampler2D texture;
uniform vec2 texOffset;   // (1/width, 1/height) — set automatically by py5
uniform float strength;

void main() {
    // Flip y: gl_FragCoord y=0 is bottom, texture y=0 is top
    vec2 uv  = gl_FragCoord.xy * texOffset;
    vec2 dir = uv - vec2(0.5, 0.5);

    float r = texture2D(texture, uv - dir * strength).r;
    float g = texture2D(texture, uv).g;
    float b = texture2D(texture, uv + dir * strength).b;

    gl_FragColor = vec4(r, g, b, 1.0);
}
