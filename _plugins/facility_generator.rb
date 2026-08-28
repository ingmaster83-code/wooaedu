require 'json'

module Jekyll
  class FacilityPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      facilities = load_json(site, '_rawdata/facilities.json')

      Jekyll.logger.info "FacilityGenerator:", "#{facilities.size}개 평생교육시설 페이지 생성 중..."
      facilities.each do |f|
        next if f['slug'].to_s.strip.empty?
        site.pages << FacilityPage.new(site, f)
      end

      site.pages << SearchIndexPage.new(site, facilities)

      Jekyll.logger.info "FacilityGenerator:", "완료 (#{facilities.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "FacilityGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class FacilityPage < Page
    def initialize(site, f)
      @site = site
      @base = site.source
      @dir  = "facility/#{f['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'facility.html')
      self.data.merge!(f)
      self.data['layout']      = 'facility'
      self.data['title']       = build_title(f)
      self.data['description'] = build_desc(f)
    end

    private

    def build_title(f)
      name = f['orgName'] || ''
      loc  = [f['doShort'], f['sigungu']].compact.join(' ')
      "#{name} #{loc} 등록정보 위치 연락처"
    end

    def build_desc(f)
      name = f['orgName'] || ''
      loc  = [f['doShort'], f['sigungu']].compact.join(' ')
      type = f['type'] || ''
      "#{loc} #{name}(#{type})의 교육청 등록 정보, 주소, 전화번호, 학력인정 여부를 확인하세요."[0, 155]
    end
  end

  class SearchIndexPage < Page
    def initialize(site, facilities)
      @site = site
      @base = site.source
      @dir  = ''
      @name = 'search_index.json'

      self.process(@name)
      self.data = { 'layout' => nil, 'sitemap' => false }

      index = facilities.map do |f|
        {
          'slug'      => f['slug'],
          'orgName'   => f['orgName'],
          'type'      => f['type'],
          'isRemote'  => f['isRemote'],
          'status'    => f['status'],
          'doShort'   => f['doShort'],
          'sigungu'   => f['sigungu'],
          'addr'      => f['addr'],
          'acbgYn'    => f['acbgYn'],
        }
      end

      self.content = index.to_json
    end

    def output   = self.content
    def render(layouts, registers); end
  end
end
