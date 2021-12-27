# Changelog


<a name="0.2.0"></a>
## [0.2.0] (2021-12-27)

### Added

- Add `--plot-suffixes` option, which specifies the comma separated list of file formats of plots.
  The default value is `pdf`.
  ([f4ef724](https://github.com/tueda/polybench/commit/f4ef724a943273098487d4b39c589ab9e5e24174))

- Add titles to generated plots.
  ([4546e98](https://github.com/tueda/polybench/commit/4546e982151597acbd289dc1735b00e2b41b7674))

### Changed

- Upgrade Rings from 2.5.7 to 2.5.8.
  ([5636e5b](https://github.com/tueda/polybench/commit/5636e5b240abf038f6a6931fb85ca60afe20ddad))

- Print the default seed in the help message.
  ([2ccd784](https://github.com/tueda/polybench/commit/2ccd784c3cbf23e6c53b084ba187cbac4cea2aca))

- Suggest the `--all` option when no solvers are specified.
  ([ddd3c19](https://github.com/tueda/polybench/commit/ddd3c198e1192fd734ffc69cb1daf9b24980332e))

### Fixed

- **reform:** fix the cargo version in `Dockerfile`.
  ([ed5e9b4](https://github.com/tueda/polybench/commit/ed5e9b437bcf93e4df7f078ef0c68cccdc2d94fa))

- **rings:** fix string conversion when the number of variables is <= 3.
  ([4ad3ccc](https://github.com/tueda/polybench/commit/4ad3ccc9ed9810a64e1b0f0dfb44c19033d3d29a))

- **singular:** workaround for a change in v4-2-1.
  ([a60eed2](https://github.com/tueda/polybench/commit/a60eed27976115502e71ee31c9e02c48b08e0591))


<a name="0.1.0"></a>
## 0.1.0 (2020-12-31)

- First public version.


[0.2.0]: https://github.com/tueda/polybench/compare/0.1.0...0.2.0
