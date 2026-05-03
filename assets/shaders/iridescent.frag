#ifdef GL_ES
precision mediump float;
#endif

uniform sampler2D texture;
uniform vec2 texOffset;
uniform float angle;
uniform float time;
uniform float strength;

vec3 hue2rgb(float h) {
    h = fract(h);
    float r = abs(h * 6.0 - 3.0) - 1.0;
    float g = 2.0 - abs(h * 6.0 - 2.0);
    float b = 2.0 - abs(h * 6.0 - 4.0);
    return clamp(vec3(r, g, b), 0.0, 1.0);
}

void main() {
    vec2 uv = gl_FragCoord.xy * texOffset;
    vec4 texColor = texture2D(texture, uv);

    float facing = abs(cos(angle));
    float sheen  = 1.0 - facing;

    float hue    = uv.x * 0.4 + time * 0.05 + sheen * 0.3;
    vec3 rainbow = hue2rgb(hue);
    vec3 result  = mix(texColor.rgb, texColor.rgb + rainbow * strength, sheen);

    gl_FragColor = vec4(result, texColor.a);
}
