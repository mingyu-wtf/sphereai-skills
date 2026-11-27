// Shape of the resolved props that scripts/render.py passes to the composition.
// All times here are already converted to frames. The human-facing format is edit.json
// (see references/edit-json.md); render.py turns edit.json into this.

export type Fit = 'cover' | 'contain' | 'blur';
export type Zoom = 'in' | 'out' | null;

export type ClipItem = {
  kind: 'video' | 'image' | 'color';
  src: string | null; // path inside public/, null for "color"
  color: string;
  from: number; // timeline start (frames)
  dur: number; // frames on the timeline
  trimBefore: number; // source frames skipped at the start (video only)
  speed: number;
  fit: Fit;
  zoom: Zoom;
  zoomAmount: number;
  volume: number;
  fadeIn: number; // frames of crossfade with the previous clip
  // Frames of the original sound's fade-in / fade-out (crossfades, and a tiny ramp at cuts to avoid clicks).
  audioFadeIn: number;
  audioFadeOut: number;
  // Part of the source to keep, as fractions of its width/height cut from each side (0 = keep all).
  crop: {top: number; bottom: number; left: number; right: number} | null;
  srcWidth: number; // source size in pixels (0 = unknown); needed for crop
  srcHeight: number;
};

export type AudioItem = {
  src: string;
  from: number;
  dur: number;
  trimBefore: number;
  volume: number;
  loop: boolean;
  fadeIn: number;
  fadeOut: number;
  // Absolute frame ranges where the volume drops by duckFactor (music only).
  duck: [number, number][];
  duckFactor: number;
  duckRamp: number;
};

export type CaptionItem = {
  text: string;
  from: number;
  dur: number;
  style: 'shorts' | 'standard';
  position: 'top' | 'center' | 'lower' | 'bottom';
  highlight: string[];
};

export type TitleItem = {
  kind: 'title' | 'lower_third';
  text: string;
  sub: string;
  from: number;
  dur: number;
  position: 'top' | 'center' | 'lower' | 'bottom';
  dim: boolean; // darken the picture behind a title card
};

export type StyleProps = {
  fontFamily: string; // full CSS font-family stack
  fontUrl: string | null; // path inside public/ of a user font file
  fontWeight: number;
  textColor: string;
  accentColor: string;
  outlineColor: string;
  boxColor: string;
  captionScale: number;
  lang: string;
};

export type EditProps = {
  width: number;
  height: number;
  fps: number;
  durationInFrames: number;
  background: string;
  style: StyleProps;
  clips: ClipItem[];
  audio: AudioItem[];
  captions: CaptionItem[];
  titles: TitleItem[];
};

export const defaultProps: EditProps = {
  width: 1080,
  height: 1920,
  fps: 30,
  durationInFrames: 90,
  background: '#101014',
  style: {
    fontFamily: 'sans-serif',
    fontUrl: null,
    fontWeight: 800,
    textColor: '#FFFFFF',
    accentColor: '#FFD43B',
    outlineColor: '#000000',
    boxColor: 'rgba(0,0,0,0.55)',
    captionScale: 1,
    lang: 'en',
  },
  clips: [
    {kind: 'color', src: null, color: '#2b2d42', from: 0, dur: 90, trimBefore: 0, speed: 1, fit: 'cover', zoom: 'in', zoomAmount: 0.06, volume: 0, fadeIn: 0, audioFadeIn: 0, audioFadeOut: 0, crop: null, srcWidth: 0, srcHeight: 0},
  ],
  audio: [],
  captions: [{text: 'Run scripts/render.py with an edit.json', from: 10, dur: 70, style: 'shorts', position: 'center', highlight: ['edit.json']}],
  titles: [],
};
