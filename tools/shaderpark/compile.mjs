// usage: node compile.mjs <sculpture.js> [outdir]
// Headless Shader Park -> GLSL. Exit 0 ok, 1 sculpture/JS error (thrown by shader-park-core), 2 reported error, 3 adapter anchor missing.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { basename, join } from 'node:path';
import { sculptToGLSL, sculptToFullGLSLSource, sculptToTouchDesignerShaderSource } from 'shader-park-core';

const f = process.argv[2];
const out = process.argv[3] || 'out';
const name = basename(f, '.js');
const src = readFileSync(f, 'utf8');
mkdirSync(out, { recursive: true });

const g = sculptToGLSL(src);
if (g.error) { console.error('COMPILE ERROR:', g.error); process.exit(2); }

// 1. standalone WebGL2 fragment (what shaderpark.com / the minimal renderer runs)
const full = sculptToFullGLSLSource(src);
writeFileSync(join(out, name + '.full.frag'), full);

// 2. the library's own TouchDesigner GLSL MAT fragment (what the official .tox uses)
const td = sculptToTouchDesignerShaderSource(src);
if (td.error) { console.error('TD ERROR:', td.error); process.exit(2); }
writeFileSync(join(out, name + '.td_mat.frag'), td.frag);
writeFileSync(join(out, name + '.vert'), td.vert);

// 3. UNTESTED in TD: mechanical adaptation of (1) for a GLSL TOP.
const NL = String.fromCharCode(10);
const anchors = [
  '#version 300 es' + NL,
  'in vec3 sculptureCenter;',
  'out vec4 pc_fragColor;',
  'uniform vec2 resolution;',
  'uniform mat4 projectionMatrix;' + NL,
  'discard;',
];
for (const a of anchors) {
  if (!full.includes(a)) { console.error('adapter anchor missing: ' + JSON.stringify(a)); process.exit(3); }
}
const top = full
  .replace(anchors[0], '')
  .replace('precision highp float;' + NL, '')
  .replace(anchors[4], '')
  .replace(anchors[1], 'const vec3 sculptureCenter = vec3(0.0);')
  .replace(anchors[2], 'layout(location = 0) out vec4 pc_fragColor;')
  .replace(anchors[3], '#define resolution uTDOutputInfo.res.zw')
  .replace(anchors[5], '{ pc_fragColor = vec4(0.0); return; }');
writeFileSync(join(out, name + '.top.glsl'), top);

writeFileSync(join(out, name + '.uniforms.json'), JSON.stringify(g.uniforms, null, 1));
console.log(name, 'ok; uniforms:', g.uniforms.map(u => u.type + ' ' + u.name).join(', '));
