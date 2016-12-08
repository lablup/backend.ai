source 'https://rubygems.org'
gemspec

gem 'jekyll'
gem 'jekyll-paginate'
gem 'kramdown'
gem 'pygments.rb'

source 'https://rubygems.org'

require 'json'
require 'open-uri'
versions = JSON.parse(open('https://pages.github.com/versions.json').read)

gem 'github-pages', versions['github-pages']
