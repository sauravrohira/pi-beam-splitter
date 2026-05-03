#ifdef GL_ES
precision mediump float;
#endif

uniform sampler2D texture;
uniform vec2 texOffset;
uniform float angle;
uniform float power;
uniform vec3 glowColor;

void main() {
    vec2 uv = gl_FragCoord.xy * texOffset;
    vec4 texColor = texture2D(texture, uv);

    float facing  = abs(cos(angle));
    float fresnel = pow(1.0 - facing, power);

    vec2  fromCenter = abs(uv - vec2(0.5, 0.5)) * 2.0;
    float edgeMask   = max(fromCenter.x, fromCenter.y);

    vec3 result = texColor.rgb + glowColor * fresnel * edgeMask;
    gl_FragColor = vec4(result, texColor.a);
}
