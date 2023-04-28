import { useEffect } from 'preact/hooks';

export type HypothesisClientProps = {
  src?: string;
  config?: object;
};

/**
 * A component which loads the Hypothesis client into the current page.
 */
export default function HypothesisClient({
  src = 'https://hypothes.is/embed.js',
  config = {},
}: HypothesisClientProps) {
  useEffect(() => {
    // TODO - Unload the client when unmounted
  }, []);

  const clientConfig = JSON.stringify(config);
  return (
    <>
      <script className="js-hypothesis-config">{clientConfig}</script>
      <script src={src} />
    </>
  );
}
