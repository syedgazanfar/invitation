/**
 * Device fingerprint for guest registration (anti-duplicate counting).
 * Port of the legacy src/hooks/useFingerprint.ts as a plain async function:
 * same components and hash, so a device keeps the same fingerprint.
 *
 * The backend checks uniqueness on (invitation, fingerprint) with an
 * IP + User-Agent fallback; never skip sending it.
 */

export interface FingerprintResult {
  fingerprint: string;
  screen_resolution: string;
  timezone_offset: string;
  languages: string;
  canvas_hash: string;
}

function hashString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(8, '0');
}

function canvasData(): string {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';
    canvas.width = 200;
    canvas.height = 50;
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(0, 0, 200, 50);
    ctx.fillStyle = '#069';
    ctx.fillText('Digital Invitation Platform', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Fingerprint', 4, 17);
    return canvas.toDataURL();
  } catch {
    return '';
  }
}

function webglData(): string {
  try {
    const canvas = document.createElement('canvas');
    const gl = (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')) as WebGLRenderingContext | null;
    if (!gl) return '';
    const info = gl.getExtension('WEBGL_debug_renderer_info');
    if (!info) return '';
    return `${gl.getParameter(info.UNMASKED_VENDOR_WEBGL)}-${gl.getParameter(info.UNMASKED_RENDERER_WEBGL)}`;
  } catch {
    return '';
  }
}

export async function getFingerprint(): Promise<FingerprintResult> {
  const canvas = canvasData();
  const components = {
    userAgent: navigator.userAgent,
    screenResolution: `${window.screen.width}x${window.screen.height}x${window.screen.colorDepth}`,
    timezoneOffset: new Date().getTimezoneOffset().toString(),
    languages: navigator.languages?.join(',') || navigator.language,
    canvasHash: canvas,
    webglHash: webglData(),
    platform: navigator.platform,
  };

  return {
    fingerprint: hashString(Object.values(components).join('|')),
    screen_resolution: components.screenResolution,
    timezone_offset: components.timezoneOffset,
    languages: components.languages,
    canvas_hash: canvas ? hashString(canvas) : '',
  };
}
