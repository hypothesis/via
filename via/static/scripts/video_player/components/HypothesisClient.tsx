import { useLayoutEffect } from 'preact/hooks';

export type HypothesisClientProps = {
  /** URL of the client's boot script. */
  src?: string;

  /**
   * Configuration to pass to the Hypothesis client via the `hypothesisConfig`
   * global [1].
   *
   * Note that changing this has no effect once the client is started and read
   * its configuration.
   *
   * [1] https://h.readthedocs.io/projects/client/en/latest/publishers/config.html#configuring-the-client-using-javascript
   */
  config?: object;
};

/**
 * A component which loads the Hypothesis client into the current page.
 */
export default function HypothesisClient({
  src = 'https://hypothes.is/embed.js',
  config = {},
}: HypothesisClientProps) {
  // nb. Use a layout effect here so that variable is definitely set before
  // client's boot script executes.
  useLayoutEffect(() => {
    (window as any).hypothesisConfig = () => config;
  }, [config]);

  return <script src={src} />;
}
