import {Config} from '@remotion/cli/config';

// JPEG frames are much faster than PNG and fine for h264 output.
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);
