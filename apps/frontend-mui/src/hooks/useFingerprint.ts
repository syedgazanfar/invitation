/**
 * Device Fingerprinting Hook
 * 
 * This hook generates a unique device fingerprint for anti-fraud tracking.
 * It combines multiple browser characteristics to create a unique identifier.
 */
import { useEffect, useState, useCallback } from 'react';

interface FingerprintData {
  fingerprint: string;
  components: {
    userAgent: string;
    screenResolution: string;
    timezoneOffset: string;
    languages: string;
    canvasHash: string;
    webglHash: string;
    platform: string;
  };
}

export const useFingerprint = () => {
  const [fingerprintData, setFingerprintData] = useState<FingerprintData | null>(null);

  // Generate canvas fingerprint
  const getCanvasFingerprint = (): string => {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return '';
      
      // Draw text with different styles
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
    } catch (e) {
      return '';
    }
  };

  // Generate WebGL fingerprint
  const getWebGLFingerprint = (): string => {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return '';
      
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (!debugInfo) return '';
      
      const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
      
      return `${vendor}-${renderer}`;
    } catch (e) {
      return '';
    }
  };

  // Hash function
  const hashString = (str: string): string => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  };

  // Generate fingerprint
  const generateFingerprint = useCallback((): FingerprintData => {
    const components = {
      userAgent: navigator.userAgent,
      screenResolution: `${window.screen.width}x${window.screen.height}x${window.screen.colorDepth}`,
      timezoneOffset: new Date().getTimezoneOffset().toString(),
      languages: navigator.languages?.join(',') || navigator.language,
      canvasHash: getCanvasFingerprint(),
      webglHash: getWebGLFingerprint(),
      platform: navigator.platform,
    };

    // Combine all components
    const fingerprintString = Object.values(components).join('|');
    const fingerprint = hashString(fingerprintString);

    return {
      fingerprint,
      components,
    };
  }, []);

  useEffect(() => {
    const data = generateFingerprint();
    setFingerprintData(data);
  }, [generateFingerprint]);

  return {
    fingerprint: fingerprintData?.fingerprint || '',
    components: fingerprintData?.components,
    generateFingerprint,
  };
};

export default useFingerprint;
