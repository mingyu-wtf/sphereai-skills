import React from 'react';
import {Composition} from 'remotion';
import {Edit} from './Edit';
import {defaultProps, EditProps} from './types';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Edit"
      component={Edit}
      defaultProps={defaultProps}
      // Size, fps and length all come from the props, so one composition fits every format.
      calculateMetadata={({props}: {props: EditProps}) => ({
        width: props.width,
        height: props.height,
        fps: props.fps,
        durationInFrames: Math.max(1, Math.round(props.durationInFrames)),
      })}
    />
  );
};
