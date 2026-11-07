import type { InvitationCreateInput } from './types';

/** Matches nginx client_max_body_size (20m) with headroom for the other fields. */
export const BANNER_MAX_BYTES = 15 * 1024 * 1024;
const BANNER_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']; // Invitation.banner_image FileExtensionValidator

/** Validation message for the banner input, or null if the file is acceptable. */
export function bannerError(file: File | null): string | null {
  if (!file) return 'Please choose a banner image for your invitation.';
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  if (!BANNER_EXTENSIONS.includes(ext)) return 'Banner must be a JPG, PNG or WEBP image.';
  if (file.size > BANNER_MAX_BYTES) return `Banner must be smaller than ${BANNER_MAX_BYTES / (1024 * 1024)} MB.`;
  return null;
}

/**
 * Multipart body for POST /invitations/create/. Django requires banner_image
 * (an ImageField), so the invitation has to be sent as FormData, not JSON.
 */
export function invitationFormData(input: InvitationCreateInput, banner: File): FormData {
  const fd = new FormData();
  for (const [key, value] of Object.entries(input)) {
    if (value !== undefined && value !== null && value !== '') fd.append(key, String(value));
  }
  fd.append('banner_image', banner);
  return fd;
}
